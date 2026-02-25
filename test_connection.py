from sqlalchemy import create_engine
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        print("Connection successful!")
except Exception as e:
    print("Error:", e)