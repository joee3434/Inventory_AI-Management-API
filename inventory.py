from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, ForeignKey, text
from pydantic import BaseModel
from typing import Dict, Optional, Any
import re
import time

from database import Base, get_db
from llm_client import generate_sql

router = APIRouter()

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

def _is_safe_select_sql(sql: str) -> bool:
    low = sql.strip().lower()
    if not low.startswith("select"):
        return False

    blocked = ["insert", "update", "delete", "drop", "alter", "truncate", "exec", "merge", "create"]
    if any(b in low for b in blocked):
        return False

    allowed_tables = {"sites", "assets"}
    table_hits = re.findall(r"\b(from|join)\s+([a-zA-Z_][\w]*)", low)

    for _, table in table_hits:
        if table.lower() not in allowed_tables:
            return False

    return True

def _execute_select(db: Session, sql: str, max_rows: int = 50):
    result = db.execute(text(sql))
    rows = result.fetchmany(max_rows)
    cols = list(result.keys())

    if not rows:
        return []

    if len(rows) == 1 and len(cols) == 1:
        return rows[0][0]

    return [dict(zip(cols, row)) for row in rows]

@router.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatPayload, db: Session = Depends(get_db)):
    start_time = time.time()

    sql_res = generate_sql(payload.message)

    if sql_res["status"] == "error":
        return {
            "natural_language_answer": "LLM error occurred while generating SQL",
            "sql_query": "",
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res.get("provider", "ollama"),
            "model": sql_res.get("model", "llama3.2:1b"),
            "status": "error",
            "error": sql_res.get("error")
        }

    sql = (sql_res.get("sql_query") or "").strip()

    if not sql:
        return {
            "natural_language_answer": "I cannot answer this question using the current database schema.",
            "sql_query": "",
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res["provider"],
            "model": sql_res["model"],
            "status": "ok",
            "error": None
        }

    if not _is_safe_select_sql(sql):
        return {
            "natural_language_answer": "Unsafe SQL was blocked. Only SELECT queries are allowed.",
            "sql_query": "",
            "data": None,
            "latency_ms": int((time.time() - start_time) * 1000),
            "provider": sql_res["provider"],
            "model": sql_res["model"],
            "status": "error",
            "error": "Unsafe SQL blocked."
        }

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

    count = len(data) if isinstance(data, list) else 1

    return {
        "natural_language_answer": f"Query executed successfully. Returned {count} result(s).",
        "sql_query": sql,
        "data": data,
        "latency_ms": int((time.time() - start_time) * 1000),
        "provider": sql_res["provider"],
        "model": sql_res["model"],
        "status": "ok",
        "error": None
    }

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
