import json
import time
import requests

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"

SQL_SYSTEM = """
You are an Inventory Management SQL generator for SQL Server.

Return ONLY valid JSON (no markdown, no extra text) with exactly:
{
  "sql_query": "..."
}

Rules:
- SQL Server syntax only.
- Do NOT execute SQL.
- SELECT only. No INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/EXEC/MERGE/CREATE.
- Use ONLY these tables/columns:
  Sites(id, name, location)
  Assets(id, name, category, site_id)
- If the question cannot be answered with the schema, return:
  {"sql_query": ""}
"""

SUMMARY_SYSTEM = """
You are an inventory assistant.

Given:
- The user's question
- The SQL query (already executed)
- The execution result data (JSON)

Write a clear professional English answer.
If the result is empty, say so clearly.
Do NOT include SQL in the answer.
Keep it concise and correct.
Return ONLY plain text.
"""

def _ollama_generate(prompt: str, temperature: float = 0.2, timeout: int = 120) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature}
    }
    r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()

def generate_sql(user_question: str) -> dict:
    start = time.time()
    try:
        raw = _ollama_generate(
            f"{SQL_SYSTEM}\nUser question: {user_question}\nJSON:",
            temperature=0.1
        )
        obj = json.loads(raw)
        latency_ms = int((time.time() - start) * 1000)
        return {
            "sql_query": (obj.get("sql_query") or "").strip(),
            "latency_ms": latency_ms,
            "provider": "ollama",
            "model": OLLAMA_MODEL,
            "status": "ok"
        }
    except Exception as e:
        return {
            "sql_query": "",
            "latency_ms": int((time.time() - start) * 1000),
            "provider": "ollama",
            "model": OLLAMA_MODEL,
            "status": "error",
            "error": str(e)
        }

def summarize_answer(user_question: str, sql_query: str, data) -> dict:
    start = time.time()
    try:
        prompt = (
            f"{SUMMARY_SYSTEM}\n"
            f"User question: {user_question}\n"
            f"SQL: {sql_query}\n"
            f"Result JSON: {json.dumps(data, ensure_ascii=False)}\n"
            f"Answer:"
        )
        answer = _ollama_generate(prompt, temperature=0.2)
        latency_ms = int((time.time() - start) * 1000)
        return {
            "natural_language_answer": answer.strip(),
            "latency_ms": latency_ms,
            "provider": "ollama",
            "model": OLLAMA_MODEL,
            "status": "ok"
        }
    except Exception as e:
        return {
            "natural_language_answer": "LLM error occurred while summarizing results",
            "latency_ms": int((time.time() - start) * 1000),
            "provider": "ollama",
            "model": OLLAMA_MODEL,
            "status": "error",
            "error": str(e)
        }