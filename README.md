# Inventory AI Management API (Present Query)

This project is a minimal Inventory Management API built with **Python + FastAPI** and **SQL Server**.
It includes an AI Chat endpoint that returns:
- a natural language answer
- the exact SQL query (“present query”)

## Features
- Sites CRUD: POST /sites, GET /sites
- Assets CRUD: POST /assets, GET /assets
- AI Chat: POST /api/chat (Local LLM via Ollama + llama3)

## Tech Stack
- Python 3.13
- FastAPI + Uvicorn
- SQLAlchemy + pyodbc
- SQL Server (SQLEXPRESS)
- Ollama (Local LLM) + llama3

## How to Run
1) Install dependencies:
```bash
pip install -r requirements.txt
