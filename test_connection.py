from sqlalchemy import create_engine, text
from config import DATABASE_URL
import sys

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection successful.")
    sys.exit(0)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
