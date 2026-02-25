from llm_client import generate_sql, summarize_answer
from database import SessionLocal
from sqlalchemy import text

# Open DB session
db = SessionLocal()

prompts = [
    "How many assets do I have?",
    "How many assets by site?"
]

def execute_sql(sql: str):
    """
    Executes a SELECT query and returns:
    - scalar for single value queries (like COUNT)
    - list[dict] for multi-row/multi-column results
    """
    if not sql:
        return None

    result = db.execute(text(sql))

    # Fetch all rows at once (prevents ResourceClosedError)
    rows = result.fetchall()

    if not rows:
        return []

    # Single row + single column => scalar
    if len(rows) == 1 and len(rows[0]) == 1:
        return rows[0][0]

    # Otherwise return list of dicts
    cols = list(result.keys())
    return [dict(zip(cols, r)) for r in rows]


for question in prompts:
    print("\nQuestion:", question)

    # Step 1: Generate SQL
    sql_res = generate_sql(question)

    if sql_res.get("status") == "error":
        print("LLM Error:", sql_res.get("error"))
        continue

    sql = (sql_res.get("sql_query") or "").strip()
    print("Generated SQL:", sql)

    if not sql:
        print("Execution result: None")
        print("Final Answer: I can't answer this with the current schema.")
        continue

    # Step 2: Execute SQL
    try:
        data = execute_sql(sql)
        print("Execution result:", data)
    except Exception as e:
        print("SQL Execution Error:", str(e))
        continue

    # Step 3: Summarize Answer using real DB results
    summ = summarize_answer(question, sql, data)

    if summ.get("status") == "error":
        print("Summary error:", summ.get("error"))
    else:
        print("Final Answer:", summ.get("natural_language_answer"))


db.close()