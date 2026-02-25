import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


DATABASE_URL = (
    "mssql+pyodbc://localhost\\SQLEXPRESS/INVENTORY_AI?"
    "driver=ODBC+Driver+18+for+SQL+Server&"
    "trusted_connection=yes&"
    "Encrypt=no&"
    "TrustServerCertificate=yes"
)