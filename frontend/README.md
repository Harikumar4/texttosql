# Frontend - SQL Query Chatbot

This is the frontend part of our SQL Query Chatbot. It's built with React and TypeScript, and it gives you a chat interface to talk to your database.

## Getting Started

1. First, install all the dependencies:
   ```bash
   npm install
   ```

2. Then start the development server:
   ```bash
   npm start
   ```
   This will open the app at [http://localhost:3000](http://localhost:3000)

## What's in the Code?

Here's how the frontend is organized:
```
frontend/
├── src/
│   ├── App.tsx          
│   ├── App.css          
│   └── index.tsx        
├── public/              
├── package.json         
└── tsconfig.json        
```



## Development Notes

The frontend talks to the backend at `http://localhost:8000`. Make sure your backend is running before you start the frontend


## Working
- The app takes a message from the user and then forms a json object with structure
```
{
  "type": "user_message",
  "id": "msg-<timestamp>",
  "session_id": "session-<timestamp>-<random>",
  "payload": {
    "text": "user's input message"
  }
}

```
- This is sent to the backend , therefore backend has information of who sent it , the session id for session memory management and to get the original message
- The backend can send either of the following two jsons back as reply
1. json for chat_reply
```
{
  "type": "chat_reply",
  "id": "msg-<timestamp>",
  "session_id": "session-<timestamp>-<random>",
  "payload": {
    "text": "reply to the user_message"
  }
}

```
2. json for response to sql_queries
```
{
  "type": "result",
  "id": "msg-<timestamp>",
  "session_id": "session-<timestamp>-<random>",
  "payload": {
    "result": [
      the result for given command
    ]
  }
}
```
3. if it gets any other json other than the ones above it prints the entire json as output in the chat
