import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const Chat = ({ repoUrl }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !repoUrl) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        repo_url: repoUrl,
        question: input,
        history: messages.map(m => ({ role: m.role, content: m.content }))
      });
      const assistantMsg = { role: 'assistant', content: response.data.answer };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Error: Could not get response.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: 'var(--bg-secondary)',
      borderRadius: '24px',
      padding: '20px',
      border: '1px solid var(--card-border)',
    }}>
      <h2 style={{ marginBottom: '16px' }}>💬 Ask about the code</h2>
      <div style={{
        flex: 1,
        overflowY: 'auto',
        marginBottom: '16px',
        paddingRight: '8px',
        maxHeight: '500px',
      }}>
        {messages.length === 0 && (
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: '40px' }}>
            Ask a question about this repository.
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            marginBottom: '12px',
            display: 'flex',
            justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
          }}>
            <div style={{
              maxWidth: '80%',
              padding: '10px 14px',
              borderRadius: '16px',
              backgroundColor: msg.role === 'user' ? 'var(--accent-cyan)' : 'rgba(255,255,255,0.06)',
              color: msg.role === 'user' ? '#0b0d15' : 'var(--text-primary)',
              wordBreak: 'break-word',
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>Typing...</div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          className="input-repo"
          placeholder="Ask a question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || !repoUrl}
          style={{ flex: 1 }}
        />
        <button
          className="btn-primary"
          onClick={sendMessage}
          disabled={isLoading || !input.trim() || !repoUrl}
          style={{ padding: '10px 20px' }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;