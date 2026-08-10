import React from 'react';

const ReportViewer = ({ report, pdfBase64, txtContent }) => {
  if (!report) {
    return (
      <div className="card">
        <h2>📘 Final Report</h2>
        <div style={{ color: 'var(--text-secondary)', padding: '20px' }}>
          Report will appear here.
        </div>
      </div>
    );
  }

  const downloadFile = (content, filename, mime) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadPDF = () => {
    if (pdfBase64) {
      const byteChars = atob(pdfBase64);
      const byteArr = new Uint8Array(byteChars.length);
      for (let i = 0; i < byteChars.length; i++) byteArr[i] = byteChars.charCodeAt(i);
      downloadFile(byteArr, 'documentation.pdf', 'application/pdf');
    }
  };

  return (
    <div className="card">
      <h2>📘 Final Report</h2>
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button className="btn-outline" onClick={downloadPDF}>
          📄 Download PDF
        </button>
        <button
          className="btn-outline"
          onClick={() => downloadFile(txtContent, 'documentation.txt', 'text/plain')}
        >
          📝 Download TXT
        </button>
      </div>
      <div className="report-content">{report}</div>
    </div>
  );
};

export default ReportViewer;