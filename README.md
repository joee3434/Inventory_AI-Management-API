# Inventory Chatbot API (Present Query) — FastAPI + SQL Server + Local LLM (Ollama)

## Overview
This project implements a minimal **Inventory AI Chat Service** in **Python + FastAPI** that answers inventory/business questions and returns, for each answer, the **exact SQL query** the system would run (**“present query”**).

 **No paid API key needed** — the solution uses a **Local LLM** via **Ollama (llama3)**.

---

## Assignment Requirement (Summary)
**Core Endpoint:** `POST /api/chat`

**Request JSON**
```json
{ "session_id": "string", "message": "string", "context": {} }
