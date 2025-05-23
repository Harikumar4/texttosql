# Backend - SQL Query Chatbot

This is the backend part of our SQL Query Chatbot. It's built with Python and FastAPI, it handles the database queries and the chat session management.


## Getting Started

1. Open PowerShell and navigate to the backend folder:
   ```
   cd path\to\your\project\backend
   ```

2. Create a `.env` file in the backend folder with these settings:
   ```
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASS=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   GROQ_API_KEY=your_groq_api_key
   MODEL_NAME=model_name 
   ```

3. Create a Python virtual environment:
   ```
   python -m venv name_of_venv
   ```
4. Activate the virtual environment:
   ```
   ./name_of_venv/Scripts/Activate.ps1
   ```
5. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
6. Run the FastAPI server with uvicorn:
   ```
   uvicorn main:app --reload --log-level debug
   ```
7. The backend API will be available at: `http://localhost:8000`

## What's in the Code?

Here's how the backend is organized:
```
backend/
├── main.py           
├── models.py    
├── .env      
└── requirements.txt  
```

## API Endpoints

Here are the main ways to talk to the backend:
- `POST /chat`: Send messages and get responses
- `GET /session-stats`: Check how many active sessions we have
- `GET /session/{session_id}/history`: See what was said in a chat
- `DELETE /session/{session_id}`: Clear a chat history

## How Sessions Work

We keep track of conversations using a `SimpleSessionManager` that:
- Creates unique IDs for each chat so we know who's who
- Keeps track of everything said during a chat, so the assistant remembers context
- Automatically cleans up old or inactive chats to save resources
- Keeps an eye on how many people are chatting at the same time

## Database Stuff

The backend connects to PostgreSQL and:
- Runs SQL queries safely
- Makes the results look nice
- Handles any database errors 