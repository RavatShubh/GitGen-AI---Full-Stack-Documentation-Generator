import React, { useState } from 'react';

const RepoInput = ({ onSubmit, onRoadmap, isLoading, isRoadmapLoading, repoUrl }) => {
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim());
  };

  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <h1>📦 DocGen AI</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>
        Generate documentation, class diagrams, ER diagrams, and flowcharts from any GitHub repo.
      </p>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <input
          type="text"
          className="input-repo"
          placeholder="https://github.com/username/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={isLoading}
          style={{ flex: 1, minWidth: '220px' }}
        />
        <button type="submit" className="btn-primary" disabled={isLoading || !url}>
          {isLoading ? '⏳ Generating...' : '🚀 Generate'}
        </button>
        {repoUrl && (
          <button 
            type="button" 
            className="btn-outline" 
            onClick={() => onRoadmap(repoUrl)}
            disabled={isRoadmapLoading}
            style={{ borderColor: '#a78bfa', color: '#a78bfa' }}
          >
            {isRoadmapLoading ? '⏳ Loading...' : '🗺️ Learn/Roadmap'}
          </button>
        )}
      </form>
    </div>
  );
};

export default RepoInput;