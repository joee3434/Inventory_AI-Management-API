# Inventory AI Management API  
### Inventory Chatbot with "Present Query" Output  
Assignment – DataHub (Hady Rashad)

---

## 📌 Project Objective

Design and implement a minimal AI chat service in Python that:

- Answers inventory/business questions
- Returns the exact SQL query that would be executed ("Present Query")
- Uses SQL Server as the database
- Integrates with an AI provider (Local LLM via Ollama)

This project demonstrates:
- Natural Language → SQL generation
- Present Query output
- Safe SQL execution (SELECT only)
- Real database results summarization

---

## 🏗️ Architecture Overview

User Question  
⬇  
POST `/api/chat` (FastAPI)  
⬇  
Local LLM (Ollama + llama3) generates SQL  
⬇  
SQL Safety Gate (SELECT only)  
⬇  
SQL Server Execution  
⬇  
LLM summarizes result  
⬇  
JSON Response (Answer + SQL + Data)

---

## 🛠️ Tech Stack

- Python 3.13
- FastAPI
- Uvicorn
- SQLAlchemy
- SQL Server (SQLEXPRESS)
- ODBC Driver 18
- Ollama (Local LLM)
- llama3 model
- requests

---

## 📂 Project Structure


inventory_ai/
│
├── config.py
├── database.py
├── inventory.py
├── llm_client.py
├── server.py
├── populate_db.py
├── test_connection.py
├── test_run.py
├── requirements.txt
└── README.md


---

## 🗄️ Database Schema (Current Implementation)

### Sites
- id (Primary Key)
- name (Unique)
- location

### Assets
- id (Primary Key)
- name
- category
- site_id (Foreign Key → Sites.id)

---

## 🚀 API Endpoints

### CRUD Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /sites | Create a new site |
| GET | /sites | Get all sites |
| POST | /assets | Create a new asset |
| GET | /assets | Get all assets |

---

### 🤖 AI Chat Endpoint

**POST /api/chat**

#### Request Body
```json
{
  "session_id": "string",
  "message": "How many assets do I have?",
  "context": {}
}
Response Format
{
  "natural_language_answer": "You have 5 assets.",
  "sql_query": "SELECT COUNT(*) FROM Assets;",
  "data": 5,
  "latency_ms": 120,
  "provider": "ollama",
  "model": "llama3",
  "status": "ok"
}
🧠 Example Queries
1️⃣ How many assets do I have?

SQL Generated:

SELECT COUNT(*) FROM Assets;

Answer:
"You currently have 5 assets."

2️⃣ How many assets by site?

SQL Generated:

SELECT s.name AS SiteName, COUNT(a.id) AS AssetCount
FROM Sites s
JOIN Assets a ON s.id = a.site_id
GROUP BY s.name;
🔒 Security Layer

Only SELECT queries allowed

Blocks:

INSERT

UPDATE

DELETE

DROP

ALTER

EXEC

Restricted to known tables only

Prevents destructive operations

⚙️ How to Run the Project
1️⃣ Install Dependencies
pip install -r requirements.txt
2️⃣ Pull Local Model
ollama pull llama3
3️⃣ Start Server
uvicorn server:app --reload
4️⃣ Open Swagger
http://127.0.0.1:8000/docs
🧪 Test via Script
python test_run.py
🔮 Future Enhancements

Add full assignment schema (Customers, Vendors, Orders, Bills, Transactions)

Add JWT Authentication

Add logging and monitoring

Improve SQL validation with parser

Add pagination for large datasets

📎 Notes

This implementation uses Local LLM (Ollama) instead of OpenAI/Azure.

Architecture allows easy switch to OpenAI/Azure via environment variables.

Demonstrates complete “Present Query” pattern with real SQL execution.
