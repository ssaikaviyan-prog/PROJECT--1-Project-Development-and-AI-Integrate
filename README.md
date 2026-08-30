# Vision-Language Autonomous Navigation System with AI Assistant and RAG

An intelligent autonomous navigation system combining Computer Vision, Gemini AI, RAG (Retrieval-Augmented Generation), ChromaDB Vector Database, Document Analyzer, Model Context Protocol (MCP) Tools, and an interactive UI Dashboard.

---

## 1. Objective
Demonstrate how an intelligent machine can sense environments, understand context, retrieve knowledge, reason safety parameters, make real-time spatial decisions, and communicate via a natural language assistant:

$$\text{Sense} \longrightarrow \text{Understand} \longrightarrow \text{Retrieve Knowledge} \longrightarrow \text{Reason} \longrightarrow \text{Decide} \longrightarrow \text{Act}$$

---

## 2. Features
- **Gemini API Integration**: Multimodal LLM reasoning for text and visual scene interpretation.
- **Automated Gemini Embeddings**: Document chunking (800–1200 chars, 100–200 overlap) with automatic `gemini-embedding-001` vector generation.
- **Local ChromaDB Vector Database**: Persistent local vector store located at `data/vector_db/`.
- **Retrieval-Augmented Generation (RAG)**: Query similarity search returning top context chunks with explicit document source citations.
- **Document Analyzer**: Multi-format document parser supporting PDF (PyMuPDF), DOCX (python-docx), and TXT files.
- **Computer Vision Perception Module**: OpenCV spatial contour analysis, obstacle bounding box calculation, direction classification, and distance estimation.
- **Autonomous Navigation Decision Engine**: Safety state machine evaluating collision risks and executing actions (`MOVE FORWARD`, `TURN LEFT`, `TURN RIGHT`, `STOP`).
- **Model Context Protocol (MCP) Tools**: Modular tool registry (`get_camera_status`, `analyze_scene`, `search_documents`, `get_navigation_status`, `get_sensor_status`, `get_project_information`).
- **Turn-Key Web Dashboard**: Dark-mode glassmorphic single-page application served by FastAPI.

---

## 3. Architecture

```text
                                  USER INTERFACE
                               (Frontend Dashboard)
                                        │
                                        ▼
                               FASTAPI REST BACKEND
                                        │
      ┌─────────────────┬───────────────┼───────────────┬────────────────┐
      │                 │               │               │                │
      ▼                 ▼               ▼               ▼                ▼
Vision Perception   Navigation     RAG Engine     Document Analyzer  MCP Tools
 (OpenCV + Vision)  Controller     (Gemini LLM)   (PDF/DOCX/TXT)    (Registry)
      │                 │               │               │                │
      └─────────┬───────┘               ▼               ▼                │
                │                 Vector Search   Chunking & Vector      │
                │                       │               │                │
                ▼                       └───────┬───────┘                │
         Gemini Reasoning                       ▼                        │
         (Safety Actions)               ChromaDB Local Vector            │
                │                         (data/vector_db)               │
                └───────────────────────────────┴────────────────────────┘
```

---

## 4. Technologies
- **Backend Framework**: Python 3.14 + FastAPI + Uvicorn
- **AI & LLM**: Google Gemini API (`gemini-1.5-flash` / REST API)
- **Embeddings**: Gemini Embedding API (`gemini-embedding-001`)
- **Vector Storage**: ChromaDB (Local persistent vector database)
- **Computer Vision**: OpenCV (`opencv-python`) + NumPy
- **Document Extractors**: PyMuPDF (`fitz`), python-docx
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism), ES6 JavaScript

---

## 5. Getting Started

### 1. Configure Environment
Copy `.env.example` to `.env` and paste your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
HOST=0.0.0.0
PORT=8000
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Backend & Dashboard
```bash
python -m backend.main
```

Access the application dashboard at:
- **Frontend Dashboard**: `http://localhost:8000`
- **Swagger API Docs**: `http://localhost:8000/docs`

---

## 6. Automated Testing
Run the 8-stage verification test suite:

```bash
python -m tests.test_system
```

Verification stages tested:
1. Gemini API Connection
2. Embedding Generation
3. ChromaDB Insertion & Retrieval
4. Document Parser & Intelligent Chunker
5. RAG Semantic Search
6. AI Chatbot Synthesis with Sources
7. Computer Vision Scene Analysis
8. Autonomous Navigation Decision Engine

---

## 7. Limitations & Future Enhancements
- **Hardware Integration**: Software simulation prototype designed for straightforward integration with ROS2 (Robot Operating System) and physical LiDAR/microcontrollers.
- **Dynamic Obstacle Tracking**: Future updates can include Kalman filter velocity tracking for moving obstacles.
