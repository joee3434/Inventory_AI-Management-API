from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, text
from pydantic import BaseModel
from typing import Dict, Optional, Any, List
import re
import time

from database import Base, get_db
from llm_client import generate_sql, summarize_answer

router = APIRouter()

# -------------------------
# Database Models
# -------------------------
class Site(Base):
    __tablename__ = "Sites"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    location = Column(String(200))

class Asset(Base):
    __tablename__ = "Assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(100))
    site_id = Column(Integer, ForeignKey("Sites.id"), nullable=False)

# -------------------------
# Pydantic Models
# -------------------------
class ChatPayload(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict] = {}

class ChatResponse(BaseModel):
    natural_language_answer: str
    sql_query: str
    data: Any
    latency_ms: int
    provider: str
    model: str
    status: str
    error: Optional[str] = None

# -------------------------
# SQL Safety Gate (SELECT-only)
# -------------------------
def _is_safe_select_sql(sql: str) -> bool:
    if not sql:
        return True

    s = sql.strip()
    if not s:
        return True

    low = s.lower()

    # must start with select
    if not low.startswith("select"):
        return False

    blocked = [
        "insert", "update", "delete", "drop", "alter", "truncate",
        "exec", "merge", "create", "grant", "revoke"
    ]
    if any(b in low for b in blocked):
        return False

    # allow only Sites/Assets after FROM/JOIN (simple but effective for your schema)
    allowed_tables = {"sites", "assets"}
    table_hits = re.findall(r"\b(from|join)\s+([a-zA-Z_][\w]*)", low)
    for _, t in table_hits:
        if t.lower() not in allowed_tables:
            return False

    return True

def _execute_select(db: Session, sql: str, max_rows: int = 50):
    """
    Executes SELECT query safely and returns:
    - scalar for single value queries
    - list[dict] for tabular results (up to max_rows)
    """
    result = db.execute(text(sql))

    # Try scalar (COUNT, etc.)
    row = result.first()
    if row is None:
        return []

    # If single column and single row: return scalar
    if len(row) == 1:
        return row[0]

    # Otherwise treat as table
    cols = list(result.keys())
    rows = [dict(zip(cols, row))]

    # Fetch more rows (we already took first row)
    for _ in range(max_rows - 1):
        nxt = result.fetchone()
        if nxt is None:
            break
        rows.append(dict(zip(cols, nxt)))

    return rows

# -------------------------
# Advanced Chat Endpoint (LLM -> SQL -> Execute -> Summarize)
# -------------------------
@router.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatPayload, db: Session = Depends(get_db)):
    start_time = time.time()

    # 1) Generate SQL
    sql_res = generate_sql(payload.message)
    if sql_res["status"] == "error":
        return {
            "natural_language_answer": "LLM error occurred while generating SQL",
            "sql_query": "",
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res.get("provider", "ollama"),
            "model": sql_res.get("model", "llama3"),
            "status": "error",
            "error": sql_res.get("error")
        }

    sql = (sql_res.get("sql_query") or "").strip()
    if not sql:
        return {
            "natural_language_answer": "I can't answer this with the current database schema (Sites, Assets).",
            "sql_query": "",
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res["provider"],
            "model": sql_res["model"],
            "status": "ok"
        }

    # 2) Safety gate
    if not _is_safe_select_sql(sql):
        return {
            "natural_language_answer": "Unsafe SQL was generated. Only SELECT queries are allowed.",
            "sql_query": "",
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res["provider"],
            "model": sql_res["model"],
            "status": "error",
            "error": "Unsafe SQL (blocked by safety gate)."
        }

    # 3) Execute SQL
    try:
        data = _execute_select(db, sql, max_rows=50)
    except Exception as e:
        return {
            "natural_language_answer": "SQL execution failed.",
            "sql_query": sql,
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res["provider"],
            "model": sql_res["model"],
            "status": "error",
            "error": str(e)
        }

    # 4) Summarize with LLM using real data
    summ = summarize_answer(payload.message, sql, data)
    if summ["status"] == "error":
        # fallback: return raw data + generic answer
        answer = "Query executed successfully. Please check returned data."
        provider = summ.get("provider", sql_res["provider"])
        model = summ.get("model", sql_res["model"])
        status = "ok"
        error = summ.get("error")
    else:
        answer = summ["natural_language_answer"]
        provider = summ["provider"]
        model = summ["model"]
        status = "ok"
        error = None

    latency_ms = int((time.time() - start_time) * 1000)
    return {
        "natural_language_answer": answer,
        "sql_query": sql,
        "data": data,
        "latency_ms": latency_ms,
        "provider": provider,
        "model": model,
        "status": status,
        "error": error
    }

# -------------------------
# CRUD for Sites
# -------------------------
@router.post("/sites")
def create_site(name: str, location: str, db: Session = Depends(get_db)):
    try:
        existing = db.query(Site).filter(Site.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Site '{name}' already exists")
        site = Site(name=name, location=location)
        db.add(site)
        db.commit()
        db.refresh(site)
        return site
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sites")
def get_sites(db: Session = Depends(get_db)):
    return db.query(Site).all()

# -------------------------
# CRUD for Assets
# -------------------------
@router.post("/assets")
def create_asset(name: str, category: str, site_id: int, db: Session = Depends(get_db)):
    try:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail=f"Site with id {site_id} not found")

        asset = Asset(name=name, category=category, site_id=site_id)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/assets")
def get_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()