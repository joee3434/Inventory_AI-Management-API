# Inventory_AI Management API

## Project Overview
Inventory_AI Management API is a lightweight inventory management system designed with FastAPI and SQLAlchemy.  
It allows management of **Sites** and **Assets**, providing CRUD operations and a mock AI chatbot endpoint for querying inventory data.  

This project is prepared for integration with an AI-based query engine (OpenAI API or Azure) in the future once a paid API key is available.

---

## Features

- **CRUD Operations**
  - Create, read Sites
  - Create, read Assets
  - Assets are linked to Sites via foreign key relationship

- **Mock AI Chatbot**
  - Provides answers to simple inventory questions
  - Returns mock SQL queries for demonstration purposes
  - Can be easily upgraded to a real AI-powered system when an API key is available

---

## Project Structure
