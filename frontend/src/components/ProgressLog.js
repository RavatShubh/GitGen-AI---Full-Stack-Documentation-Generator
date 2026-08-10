import React from 'react';

const ProgressLog = ({ logs }) => {
  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <h2>🔄 Progress</h2>
      <div className="progress-log">
        {logs.length === 0 && (
          <span style={{ color: 'var(--text-secondary)' }}>Waiting for input...</span>
        )}
        {logs.map((log, idx) => (
          <div key={idx} className="log-item">
            <span className="icon">▸</span> {log}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressLog;