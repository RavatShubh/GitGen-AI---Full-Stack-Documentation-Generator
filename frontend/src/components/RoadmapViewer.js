import React from 'react';

const RoadmapViewer = ({ roadmapData }) => {
  if (!roadmapData || !roadmapData.text_summary) return null;

  return (
    <div className="card" style={{ 
      marginBottom: '24px', 
      borderColor: 'rgba(167, 139, 250, 0.3)',
      background: 'linear-gradient(135deg, rgba(20, 28, 50, 0.9), rgba(15, 20, 40, 0.9))'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0 }}>🗺️ Learning Roadmap</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Step-by-step guide to learn this repository
          </p>
        </div>
        <button
          className="btn-outline"
          onClick={() => {
            const blob = new Blob([roadmapData.text_summary], { type: 'text/markdown' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'roadmap.md';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          }}
          style={{ borderColor: '#a78bfa', color: '#a78bfa' }}
        >
          📥 Download as Markdown
        </button>
      </div>
      
      <div className="report-content" style={{ maxHeight: '600px', overflowY: 'auto' }}>
        {roadmapData.text_summary}
      </div>
    </div>
  );
};

export default RoadmapViewer;