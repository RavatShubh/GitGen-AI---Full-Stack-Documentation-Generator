import { useState, useRef, useCallback } from 'react';

export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [progress, setProgress] = useState([]);
  const [finalData, setFinalData] = useState(null);
  const ws = useRef(null);

  const connect = useCallback((repoUrl, diagramTypes = []) => {
    return new Promise((resolve, reject) => {
      ws.current = new WebSocket(url);
      
      ws.current.onopen = () => {
        setIsConnected(true);
        ws.current.send(JSON.stringify({ repo_url: repoUrl, diagram_types: diagramTypes }));
        resolve();
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("WebSocket message:", data);
        
        if (data.type === 'status' || data.type === 'progress') {
          setProgress(prev => [...prev, data.message || data.step]);
          setMessages(prev => [...prev, data]);
        } else if (data.type === 'complete') {
          setFinalData(data);
          setProgress(prev => [...prev, "✅ Done!"]);
        } else if (data.type === 'error') {
          setProgress(prev => [...prev, `❌ Error: ${data.message}`]);
        }
      };

      ws.current.onerror = (error) => {
        setIsConnected(false);
        reject(error);
      };

      ws.current.onclose = () => {
        setIsConnected(false);
      };
    });
  }, [url]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
    }
  }, []);

  return { isConnected, messages, progress, finalData, connect, disconnect };
};