# MedFlow Studio 🚀

**AI-Native Healthcare Workflow & Microservice Generation Platform**

MedFlow Studio is a powerful, enterprise-ready platform designed to bridge the gap between healthcare data engineering and microservice deployment. It allows users to design complex medical data flows visually and automatically generate high-performance, production-ready Python microservices.

---

## ✨ Key Features

- **Intuitive Visual Designer**: Build data pipelines using a drag-and-drop interface powered by **React Flow**.
- **AI-Powered Code Generation**: Leverage the **Gemini 2.0 Flash** model to generate entire FastAPI microservices directly from your visual designs.
- **Robust Execution Engine**: Asynchronous job handling using **Celery** and **Redis** for reliable, long-running data transformations.
- **Microservice Packaging**: One-click "Download ZIP" provides you with a complete, containerized project including:
    - **FastAPI** entry points
    - **Pydantic** data models
    - **PostgreSQL** integration
    - **Docker Compose** configuration
- **Healthcare First**: Built-in support for medical data standards, patient record management, and secure dataset handling.

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Task Queue**: Celery + Redis
- **AI Engine**: Google Gemini AI (Vertex AI / Google Generative AI)
- **Migrations**: Alembic

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **Interactions**: React Flow (Workflow Designer)
- **State Management**: TanStack Query (React Query)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Uvicorn

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key (for AI generation)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/medflow-studio.git
   cd medflow-studio
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@db:5432/medflow
   REDIS_URL=redis://redis:6379/0
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Launch the platform**:
   ```bash
   docker-compose up -d --build
   ```

4. **Access the Studio**:
   - **Frontend**: [http://localhost:3000](http://localhost:3000)
   - **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📋 Project Structure

```text
├── app/                  # FastAPI Backend source
│   ├── ai/               # AI clients and prompts
│   ├── compiler/         # Workflow-to-Code translation engine
│   ├── routes/           # API endpoints
│   └── tasks/            # Celery background workers
├── frontend/             # Next.js 14 application
│   ├── src/app/          # Routes (Protected & Public)
│   ├── src/components/   # Design System & Flow Components
│   └── src/lib/          # API hooks and utilities
└── docker-compose.yml    # Full stack orchestration
```

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

Developed with ❤️ by the MedFlow Team.
