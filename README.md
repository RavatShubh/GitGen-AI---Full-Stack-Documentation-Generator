# 🚀 GitGen AI - Full-Stack Documentation Generator

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)](https://reactjs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-orange.svg)](https://langchain.com/)
[![Cohere](https://img.shields.io/badge/Cohere-AI-purple.svg)](https://cohere.ai/)

**GitGen AI** is an intelligent documentation generator that automatically analyzes GitHub repositories and produces comprehensive documentation, architectural diagrams, learning roadmaps, and interactive Q&A capabilities—all powered by AI. Transform weeks of manual documentation work into minutes of automated analysis.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#️-tech-stack)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Screenshots](#-screenshots)
- [Project Structure](#-project-structure)
- [Configuration](#️-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

GitGen AI addresses the common challenge of maintaining up-to-date documentation for software projects. By leveraging cutting-edge AI technologies like **LangChain**, **LangGraph**, and **Cohere LLMs**, it automatically:

- Clones and analyzes any public GitHub repository
- Extracts code metadata, classes, entities, and dependencies
- Generates UML diagrams (Class, ER, Use Case)
- Creates comprehensive project reports with gap analysis
- Builds personalized learning roadmaps
- Provides RAG-based Q&A for deep codebase understanding
- Exports documentation as PDF and TXT formats

Perfect for developers, technical writers, educators, and teams onboarding new members.

---

## ✨ Key Features

### 🔍 **Intelligent Code Analysis**
- Automatically clones GitHub repositories (public repos supported)
- Extracts project structure, classes, methods, entities, and dependencies
- Identifies user roles and business logic patterns
- Analyzes up to 200 files with content preview (10KB limit per file)

### 📊 **Automated Diagram Generation**
- **Class Diagrams**: Visualize OOP structure with relationships
- **ER Diagrams**: Database schema and entity relationships
- **Use Case Diagrams**: Actor interactions and system flows
- All diagrams generated in **Mermaid** format for easy integration

### 📝 **Comprehensive Documentation**
- **Project Overview**: Concise summary of purpose and audience
- **Key Features**: Implemented functionality breakdown
- **Gap Analysis**: Missing components and incomplete features
- **Suggestions**: Actionable recommendations for deployment, testing, security, and scaling

### 🗺️ **Learning Roadmaps**
- Step-by-step milestones for understanding the codebase
- Prerequisites, setup guides, and contribution pathways
- References to actual files in the repository

### 💬 **RAG-based Q&A Chat**
- Ask questions about the codebase in natural language
- Context-aware responses using Retrieval-Augmented Generation (RAG)
- Business and technical analysis (e.g., "What companies would use this?")
- Conversation history maintained across sessions

### 🌐 **Real-time Streaming**
- WebSocket-based progress updates during analysis
- Live status messages for each processing step
- No page refresh needed—smooth UX

### 📥 **Export Capabilities**
- **PDF Export**: Professional documentation with embedded diagrams
- **TXT Export**: Plain text version for archival
- One-click download after generation

---

## 🛠️ Tech Stack

### **Backend**
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[LangChain](https://langchain.com/)** - LLM orchestration framework
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Multi-agent workflow management
- **[Cohere](https://cohere.ai/)** - Large Language Model for analysis and generation
- **[GitPython](https://gitpython.readthedocs.io/)** - Git repository interaction
- **[ReportLab](https://www.reportlab.com/)** - PDF generation
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation

### **Frontend**
- **[React.js](https://reactjs.org/)** - UI framework
- **[Mermaid](https://mermaid-js.github.io/)** - Diagram rendering
- **[Axios](https://axios-http.com/)** - HTTP client
- **WebSocket** - Real-time communication

### **AI/ML Components**
- **Cohere Command-R** model for text generation
- **RAG (Retrieval-Augmented Generation)** for context-aware chat
- **JSON-mode LLM** for structured metadata extraction

---

## 🏗️ Architecture

GitGen AI uses a **multi-agent LangGraph workflow** with the following pipeline:

```
1. fetch_context    → Clone repo & extract file tree
2. analyze_code     → Extract metadata using Cohere LLM
3. generate_diagrams → Create Mermaid diagrams (Class, ER, Use Case)
4. compile_report   → Generate comprehensive markdown report
5. export_files     → Produce PDF and TXT outputs
```

**Frontend → Backend Communication:**
- WebSocket for streaming progress updates
- REST API for chat and roadmap generation
- In-memory caching for fast repeated queries

---

## 📦 Installation

### **Prerequisites**
- Python 3.9 or higher
- Node.js 16 or higher
- Git installed
- Cohere API key ([Get one here](https://cohere.ai/))

### **1. Clone the Repository**

```bash
git clone https://github.com/RavatShubh/GitGen-AI---Full-Stack-Documentation-Generator.git
cd GitGen-AI---Full-Stack-Documentation-Generator
```

### **2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo COHERE_API_KEY=your_cohere_api_key_here > .env
echo COHERE_MODEL=command-r >> .env
```

### **3. Frontend Setup**

```bash
cd ../frontend

# Install dependencies
npm install
```

---

## 🚀 Usage

### **1. Start the Backend Server**

```bash
cd backend
# Activate venv if not already active
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### **2. Start the Frontend**

```bash
cd frontend
npm start
```

Frontend will be available at: `http://localhost:3000`

### **3. Generate Documentation**

1. Open `http://localhost:3000` in your browser
2. Enter a public GitHub repository URL (e.g., `https://github.com/username/repo`)
3. Click **"Analyze Repository"**
4. Watch real-time progress as the AI processes your repo
5. View generated diagrams, reports, and roadmaps
6. Use the chat feature to ask questions about the code
7. Download PDF or TXT documentation

---

## 📡 API Endpoints

### **WebSocket**
- `ws://localhost:8000/ws` - Streaming agent execution

### **REST API**

#### `POST /chat`
Ask questions about a processed repository.

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "question": "What is the main purpose of this project?",
  "history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous answer"}
  ]
}
```

**Response:**
```json
{
  "answer": "This project is a..."
}
```

#### `POST /roadmap`
Generate a learning roadmap for the repository.

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo"
}
```

**Response:**
```json
{
  "text_summary": "# Learning Roadmap\n## Milestone 1: Setup..."
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

---

## 📸 Screenshots

### Main Dashboard
![Dashboard](https://via.placeholder.com/800x400?text=GitGen+AI+Dashboard)

### Generated Diagrams
![Diagrams](https://via.placeholder.com/800x400?text=Class+%26+ER+Diagrams)

### Chat Interface
![Chat](https://via.placeholder.com/800x400?text=RAG-based+Q%26A)

---

## 📂 Project Structure

```
GitGen-AI/
├── backend/
│   ├── app/
│   │   ├── agent.py              # LangGraph multi-agent workflow
│   │   ├── main.py               # FastAPI application
│   │   ├── config.py             # Configuration management
│   │   ├── utils.py              # PDF/TXT generation utilities
│   │   ├── mcp_github_server.py  # GitHub MCP integration (optional)
│   │   └── __init__.py
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Environment variables (create this)
│   └── venv/                     # Virtual environment
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.js           # Q&A chat interface
│   │   │   ├── DiagramViewer.js  # Mermaid diagram renderer
│   │   │   ├── ProgressLog.js    # Real-time progress display
│   │   │   ├── RepoInput.js      # Repository URL input
│   │   │   ├── ReportViewer.js   # Documentation viewer
│   │   │   └── RoadmapViewer.js  # Learning roadmap display
│   │   ├── hooks/
│   │   │   └── useWebSocket.js   # WebSocket connection hook
│   │   ├── App.js                # Main application
│   │   ├── index.js              # Entry point
│   │   └── index.css             # Global styles
│   ├── package.json              # Node dependencies
│   └── node_modules/
│
├── .gitignore
└── README.md
```

---

## ⚙️ Configuration

### **Backend Environment Variables**

Create a `.env` file in the `backend/` directory:

```env
# Required
COHERE_API_KEY=your_cohere_api_key_here

# Optional (defaults shown)
COHERE_MODEL=command-r
```

### **Frontend Configuration**

The frontend proxies API requests to `http://localhost:8000` (configured in `package.json`).

To change the backend URL for production:

```json
// In package.json
"proxy": "https://your-backend-domain.com"
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/AmazingFeature`
3. **Commit your changes**: `git commit -m 'Add some AmazingFeature'`
4. **Push to the branch**: `git push origin feature/AmazingFeature`
5. **Open a Pull Request**

### **Ideas for Contributions**
- Support for private repositories (GitHub token authentication)
- Additional diagram types (Sequence, State, Deployment)
- Support for GitLab, Bitbucket, and other platforms
- Enhanced chat with code snippet highlighting
- Multi-language support (currently English-focused)
- Database integration for caching processed repos
- Docker containerization
- CI/CD pipeline setup

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[Cohere](https://cohere.ai/)** for providing powerful LLM capabilities
- **[LangChain](https://langchain.com/)** for the orchestration framework
- **[Mermaid](https://mermaid-js.github.io/)** for beautiful diagram rendering
- **[FastAPI](https://fastapi.tiangolo.com/)** for the excellent Python web framework

---

## 📧 Contact

**Developer**: Shubh Ravat  
**GitHub**: [@RavatShubh](https://github.com/RavatShubh)  
**Project Link**: [https://github.com/RavatShubh/GitGen-AI---Full-Stack-Documentation-Generator](https://github.com/RavatShubh/GitGen-AI---Full-Stack-Documentation-Generator)

---

## 🌟 Star this repository if you find it useful!

Made with ❤️ by Shubh Ravat
