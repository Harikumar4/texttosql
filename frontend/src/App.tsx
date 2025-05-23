import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputText;
    setInputText('');
    setIsLoading(true);

    try {
      const uniqueId = `msg-${Date.now()}`;

      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          type: 'user_message',
          id: uniqueId,
          session_id: sessionId,
          payload: { text: currentInput },
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      let botText = '';
      if (data.type === 'chat_reply' && data.payload?.text) {
        botText = data.payload.text;
      } else if (data.type === 'result') {
        botText = `SQL Query Result:\n${JSON.stringify(data.payload.result, null, 2)}`;
      } else {
        botText = JSON.stringify(data, null, 2);
      }

      const botMessage: Message = {
        id: Date.now() + 1,
        text: botText,
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: Date.now() + 2,
        text: `Error: ${error instanceof Error ? error.message : 'Failed to connect to bot.'}`,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-purple-400 p-4">
      <div className="w-full h-full flex flex-col max-w-4xl mx-auto">
        <div className="bg-black border-2 border-purple-400 rounded-lg p-4 flex-grow flex flex-col min-h-0">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-mono">CHATBOT v1.0</h1>
            <div className="flex gap-2 items-center">
              <span className="text-xs text-gray-500 font-mono">
                Session: {sessionId.slice(-8)}
              </span>
              <button
                onClick={clearChat}
                className="bg-purple-800 hover:bg-purple-700 px-3 py-1 rounded text-xs font-mono transition-colors"
              >
                CLEAR
              </button>
            </div>
          </div>
          <div className="flex-grow overflow-y-auto mb-4 font-mono space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <p>Welcome! Start a conversation...</p>
                <p className="text-xs mt-2">You can ask me to run SQL queries or chat normally.</p>
              </div>
            )}
            
            {messages.map(message => (
              <div
                key={message.id}
                className={`p-3 rounded-lg ${
                  message.sender === 'user' 
                    ? 'bg-purple-900 ml-8 border-l-4 border-purple-400' 
                    : 'bg-gray-800 mr-8 border-l-4 border-green-400'
                }`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold">
                    {message.sender === 'user' ? 'YOU' : 'BOT'}
                  </span>
                  <span className="text-xs text-gray-400">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <div 
                  className="whitespace-pre-wrap break-words"
                  style={{ wordBreak: 'break-word' }}
                >
                  {message.text}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="bg-gray-800 mr-8 p-3 rounded-lg border-l-4 border-yellow-400">
                <div className="text-xs font-bold mb-2">BOT</div>
                <div className="flex items-center space-x-2">
                  <div className="animate-spin h-4 w-4 border-2 border-purple-400 border-t-transparent rounded-full"></div>
                  <span>Thinking...</span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              disabled={isLoading}
              className="flex-1 bg-black border-2 border-purple-400 rounded px-4 py-2 text-purple-400 font-mono focus:outline-none focus:border-purple-300 disabled:opacity-50"
              placeholder={isLoading ? "Processing..." : "Type your message..."}
            />
            <button
              type="submit"
              disabled={isLoading || !inputText.trim()}
              className="bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded font-mono transition-colors"
            >
              {isLoading ? '...' : 'SEND'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;