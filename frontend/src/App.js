import React, { useState } from 'react';
import axios from 'axios';
import { useWebSocket } from './hooks/useWebSocket';
import RepoInput from './components/RepoInput';
import ProgressLog from './components/ProgressLog';
import DiagramViewer from './components/DiagramViewer';
import ReportViewer from './components/ReportViewer';
import Chat from './components/Chat';
import RoadmapViewer from './components/RoadmapViewer';
import './index.css';

const WS_URL = 'ws://localhost:8000/ws';
const API_URL = 'http://localhost:8000';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [isRoadmapLoading, setIsRoadmapLoading] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [roadmapData, setRoadmapData] = useState(null);
  const { progress, finalData, connect } = useWebSocket(WS_URL);

  const handleGenerate = async (url) => {
    setRepoUrl(url);
    setRoadmapData(null);
    setIsLoading(true);
    try {
      await connect(url);
    } catch (error) {
      console.error('Connection error:', error);
      alert('Failed to connect to server. Make sure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoadmap = async (url) => {
    if (!url) return;
    setIsRoadmapLoading(true);
    try {
      const response = await axios.post(`${API_URL}/roadmap`, { repo_url: url });
      setRoadmapData(response.data);
    } catch (error) {
      console.error('Roadmap error:', error);
      alert('Failed to generate roadmap. Make sure the repo is processed first.');
    } finally {
      setIsRoadmapLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="left-column">
        <RepoInput 
          onSubmit={handleGenerate} 
          onRoadmap={handleRoadmap}
          isLoading={isLoading}
          isRoadmapLoading={isRoadmapLoading}
          repoUrl={repoUrl}
        />
        <ProgressLog logs={progress} />
        {finalData && (
          <>
            <DiagramViewer diagrams={finalData.diagrams} />
            <ReportViewer
              report={finalData.report}
              pdfBase64={finalData.pdf_base64}
              txtContent={finalData.txt_content}
            />
            <RoadmapViewer roadmapData={roadmapData} />
          </>
        )}
      </div>

      <div className="right-column">
        {finalData ? (
          <Chat repoUrl={repoUrl} />
        ) : (
          <div className="card" style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-secondary)',
            minHeight: '300px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>💬</div>
              <p>Generate documentation first,<br />then ask questions about the code.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;