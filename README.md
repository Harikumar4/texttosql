# SQL Query Chatbot

A project made to learn mcp , This is a chatbot that helps you interact with your PostgreSQL database using natural language. Just chat with it like you would with a person, and it'll understand your questions and run the appropriate SQL queries.

This project is inspired by MCP and doesnt use the Claude's native implementation of MCP.
Instead it uses a custom MCP approach which is similar to the stucture and messages of Claude's MCP. Because this was mean to be a free-to-use tool so we use groq's api which provides free access to certain models for basic usage under certain limits.

Since these models dont natively understand MCP we format our responses in a way it follows MCP like pattern .

Use a better model for smooth functioning

## Content

The project is split into two parts:
- A React frontend that gives you a chat interface
- A Python backend that handles the database stuff and AI 

## Getting Started

1. Clone this repo:
   ```bash
   git clone https://github.com/yourusername/texttosql.git
   cd texttosql
   ```

2. Set up the backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   # Create .env file with your database and API credentials
   python main.py
   ```

3. Set up the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Configuration

You'll need to create a `.env` file in the backend folder with these settings:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASS=your_db_password
DB_HOST=localhost
DB_PORT=port_number
GROQ_API_KEY=your_groq_api_key
MODEL_NAME=model_name 
```

## How to Use

1. Type your question or request in the chat
2. The bot will understand what you want and run the right SQL query
3. You'll see the results with proper format in the chat
4. To refresh the memeory use the clear button

## Future Steps 
- [ ] Include a better session memory management instead of just storing direct prompts and messages, as it takes too much token/memory.
- [ ] Add a way to ensure regular backups since the model has full access to the database and anything can go wrong.
- [ ] Implement a tabular view of the database (like online SQL compilers) for better understanding and visualization.

For more details Check out the README files in the frontend and backend folders

## Resources
- [Implementation of Claude's native MCP to connect to PostgreSQL database](https://youtu.be/CqMV5-iOf4M?si=iGWRNOsuNSkHerSt)  