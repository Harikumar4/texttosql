# importing the requried libraries
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from groq import Groq
import traceback
import uuid
from typing import Dict, List, Optional

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# get credentials from env files
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
model_name = os.getenv("MODEL_NAME","llama3-8b-8192")

# Session Manager Class
class SimpleSessionManager:
    def __init__(self, cleanup_interval_minutes: int = 30):
        self.sessions = {} # to store sessin id and session data
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.last_cleanup = datetime.utcnow() # to mark when last cleanup happened
    
    def create_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """Get existing session or create new one"""
        if not session_id or session_id not in self.sessions:
            if not session_id:
                session_id = self.create_session_id()
            self.sessions[session_id] = {
                "history": [],
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "context": {}  
            }
        else:
            # to update last activity
            self.sessions[session_id]["last_activity"] = datetime.utcnow()
            
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        """to add a message to session history"""
        if session_id not in self.sessions:
            session_id = self.get_or_create_session(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        self.sessions[session_id]["history"].append(message)
        self.sessions[session_id]["last_activity"] = datetime.utcnow()
        
        # to limit history to prevent memory overflow
        max_messages = 100  # as of now we keep the latest 100 messages
        if len(self.sessions[session_id]["history"]) > max_messages:
            self.sessions[session_id]["history"] = self.sessions[session_id]["history"][-max_messages:]
    
    def get_session_history(self, session_id: str) -> List[dict]:
        """to return the session history"""
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id]["history"]
    
    def get_session_context(self, session_id: str) -> dict:
        """to return the data associated with a session """
        if session_id not in self.sessions:
            return {}
        return self.sessions[session_id]["context"]
    
    def update_session_context(self, session_id: str, context_data: dict):
        """update the context"""
        if session_id not in self.sessions:
            session_id = self.get_or_create_session(session_id)
        
        self.sessions[session_id]["context"].update(context_data)
        self.sessions[session_id]["last_activity"] = datetime.utcnow()
    
    def cleanup_old_sessions(self, max_age_hours: int = 1):
        """to remove session which are there for more than a hour"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for session_id, session_data in self.sessions.items():
            if session_data["last_activity"] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        self.last_cleanup = datetime.utcnow()
        return len(sessions_to_remove)
    
    def auto_cleanup(self):
        """if time since last cleanup exceeds clean up interval then clean up """
        if datetime.utcnow() - self.last_cleanup > self.cleanup_interval:
            return self.cleanup_old_sessions()
        return 0
    
    def get_session_stats(self) -> dict:
        """to get statistics about current sessions"""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() 
                                  if datetime.utcnow() - s["last_activity"] < timedelta(hours=1)]),
            "total_messages": sum(len(s["history"]) for s in self.sessions.values())
        }

session_manager = SimpleSessionManager()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for the mcp messages
class UserMessage(BaseModel):
    type: str
    id: str
    session_id: str | None
    payload: dict

class ChatReply(BaseModel):
    type: str
    id: str
    session_id: str | None
    timestamp: datetime
    payload: dict

# triggereed on validation error occrus when incoming json model doesnt match the given model structure
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("\n--- Validation Error ---")
    print(f"Path: {request.url.path}")
    print("Body received:")
    try:
        body = await request.json()
        print(body)
    except Exception:
        print("[Failed to parse body]")
    print("Error details:")
    print(exc.errors()) # prints the details of the error with with field required and what is the error type
    print("-------------------------\n")
    return await request_validation_exception_handler(request, exc)

# a function to run SQL query on Postgres and to return list of dict rows
def run_sql_query(sql_query: str):
    try:
        with psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        ) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql_query)
                if cursor.description:  
                    rows = cursor.fetchall()
                    return rows
                else:
                    return []
    except Exception as e:
        return {"error": str(e)}

# Helper to format query result into readable text (summary only)
def format_sql_result(sql_query: str, rows):
    if isinstance(rows, dict) and "error" in rows:
        return f"Error executing query: {rows['error']}"
    if not rows:
        return f"The query was executed successfully but returned no results."
    # if it is a query that asks for count then it print the the query retuned a count of __
    # else it gives the number of rows
    if sql_query.strip().lower().startswith("select count"):
        first_row = rows[0]
        count_value = None
        for key in first_row:
            if "count" in key.lower():
                count_value = first_row[key]
                break
        if count_value is not None:
            return f"The query returned a count of {count_value}."
    return f"The query returned {len(rows)} rows."

# Helper to convert rows to pretty JSON string for output
def rows_to_pretty_str(rows):
    try:
        return json.dumps(rows, indent=2)
    except Exception:
        return str(rows)


def create_enhanced_mcp_prompt(user_msg: UserMessage, conversation_history: List[dict]):
    """to create a prompt with context as well"""
    
    # Build conversation context
    context_lines = []
    for msg in conversation_history[-10:]: #use last  10 messages for context
        role = msg["role"].upper()
        content = msg["content"][:200]  # to truncate long messages to avoid token loss
        if content != msg["content"]:
            content += "..."
        context_lines.append(f"{role}: {content}")
    
    context_str = "\n".join(context_lines) if context_lines else "No previous conversation."
    user_text = user_msg.payload.get('text', '')
    
    # Check if user is asking for SQL or database related queries
    sql_keywords = ['select', 'insert', 'update', 'delete', 'create', 'drop', 'table', 'database', 'query', 'sql']
    is_sql_request = any(keyword in user_text.lower() for keyword in sql_keywords)
    
    if is_sql_request:
        return f"""
You are an SQL assistant. The user wants to run a database query.

Previous conversation context:
{context_str}

User message: "{user_text}"

Respond ONLY with this exact JSON format:
{{
  "type": "command",
  "id": "{user_msg.id}",
  "session_id": "{user_msg.session_id}",
  "timestamp": "{datetime.utcnow().isoformat()}",
  "payload": {{
    "action": "run_sql",
    "sql_query": "YOUR_SQL_QUERY_HERE"
  }}
}}

Replace YOUR_SQL_QUERY_HERE with the appropriate SQL query based on the user's request.
"""
    else:
        return f"""
You are a helpful chat assistant.

Previous conversation context:
{context_str}

User message: "{user_text}"

Respond ONLY with this exact JSON format:
{{
  "type": "chat_reply",
  "id": "{user_msg.id}",
  "session_id": "{user_msg.session_id}",
  "timestamp": "{datetime.utcnow().isoformat()}",
  "payload": {{
    "text": "YOUR_RESPONSE_HERE"
  }}
}}

Replace YOUR_RESPONSE_HERE with your helpful response to the user. Be friendly and conversational.
"""

# POST /chat endpoint
@app.post("/chat")
async def chat(mcp_message: UserMessage):
    try:
        session_manager.auto_cleanup()
        session_id = session_manager.get_or_create_session(mcp_message.session_id)
        
        # to add user message to session history
        user_text = mcp_message.payload.get("text", "")
        session_manager.add_message(session_id, "user", user_text)
        
        # build the prompt from the user message
        conversation_history = session_manager.get_session_history(session_id)
        prompt = create_enhanced_mcp_prompt(mcp_message, conversation_history)
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        model_response_text = response.choices[0].message.content.strip()

        # Parse MCP JSON from model response
        try:
            mcp_response = json.loads(model_response_text)
        except json.JSONDecodeError:
            # If JSON parse fails extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', model_response_text, re.DOTALL)
            if json_match:
                try:
                    mcp_response = json.loads(json_match.group())
                except json.JSONDecodeError:
                    raise ValueError("Could not parse JSON from model response")
            else:
                raise ValueError("No JSON found in model response")

        # to ensure requried fields exist
        if "type" not in mcp_response:
            raise ValueError("Missing 'type' field in response")

        # if sql command
        if mcp_response["type"] == "command" and mcp_response["payload"].get("action") == "run_sql":
            sql_query = mcp_response["payload"]["sql_query"]
            rows = run_sql_query(sql_query)

            explanation_text = format_sql_result(sql_query, rows)
            rows_str = rows_to_pretty_str(rows)

            bot_text = f"Executed SQL Query:\n{sql_query}\n\nResult:\n{explanation_text}\n\nFull rows:\n{rows_str}"
            
            session_manager.add_message(session_id, "bot", bot_text, {
                "sql_query": sql_query,
                "result_count": len(rows) if isinstance(rows, list) else 0
            })
            
            # making the reponse message
            reply_msg = ChatReply(
                type="chat_reply",
                id=mcp_response.get("id"),
                session_id=session_id,
                timestamp=datetime.utcnow(),
                payload={
                    "text": bot_text
                }
            )
            return reply_msg.dict()

        # Handle chat_reply returned by model directly
        elif mcp_response["type"] == "chat_reply":
            bot_text = mcp_response["payload"].get("text", "")
            
            session_manager.add_message(session_id, "bot", bot_text)
            
            chat_reply_msg = ChatReply(
                type="chat_reply",
                id=mcp_response.get("id"),
                session_id=session_id,
                timestamp=datetime.utcnow(),
                payload={"text": bot_text}
            )
            return chat_reply_msg.dict()

        else:
            # to catch any unexpected response
            print(f"Unexpected response type: {mcp_response.get('type', 'unknown')}")
            print(f"Full response: {mcp_response}")
            
            fallback_text = "I understand your message, but I'm having trouble processing it right now. Could you please try rephrasing?"
            session_manager.add_message(session_id, "bot", fallback_text)
            
            reply_msg = ChatReply(
                type="chat_reply",
                id=mcp_message.id,
                session_id=session_id,
                timestamp=datetime.utcnow(),
                payload={"text": fallback_text}
            )
            return reply_msg.dict()

    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON/Parsing error: {e}")
        print(f"Model response: {model_response_text}")
        
        user_text = mcp_message.payload.get("text", "")
        fallback_text = f"Nice to meet you! I received your message but had some trouble processing it. Feel free to ask me anything or request database queries."
        session_manager.add_message(session_id, "bot", fallback_text)
        
        reply_msg = ChatReply(
            type="chat_reply",
            id=mcp_message.id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            payload={"text": fallback_text}
        )
        return reply_msg.dict()
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        
        session_id = session_manager.get_or_create_session(mcp_message.session_id)
        error_text = "I'm experiencing some technical difficulties. Please try again."
        session_manager.add_message(session_id, "bot", error_text)
        
        reply_msg = ChatReply(
            type="chat_reply",
            id=mcp_message.id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            payload={"text": error_text}
        )
        return reply_msg.dict()

@app.get("/session-stats")
async def get_session_stats():
    return session_manager.get_session_stats()


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get history for a specific session"""
    history = session_manager.get_session_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "history": history
    }


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session"""
    if session_id in session_manager.sessions:
        del session_manager.sessions[session_id]
        return {"message": f"Session {session_id} cleared successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MCP Chat API is running",
        "endpoints": {
            "chat": "POST /chat - Send chat messages",
            "session_stats": "GET /session-stats - Get session statistics",
            "session_history": "GET /session/{session_id}/history - Get session history",
            "clear_session": "DELETE /session/{session_id} - Clear specific session"
        }
    }