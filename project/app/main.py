"""
HealthOps Studio — FastAPI Application Entry Point

This is the root of the backend API. It:
1. Creates the FastAPI app instance
2. Registers middleware (CORS, security headers, etc.)
3. Includes all route modules
4. Runs startup tasks (like creating default DB data)
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import auth, patients, workflows, ai, admin, jobs, datasets
from app.middleware import SecurityHeadersMiddleware, CorrelationIdMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
from app.logging_config import setup_logging, get_logger

settings = get_settings()


# ── Startup / Shutdown Events ─────────────────────────────
# lifespan replaces the deprecated @app.on_event("startup") pattern.
# Code before yield runs on startup; code after runs on shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure logging + create tables
    setup_logging()
    logger = get_logger("healthops.startup")

    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created")
    yield
    # Shutdown
    logger.info("Shutting down HealthOps Studio")


# ── App Instance ──────────────────────────────────────────
app = FastAPI(
    title="HealthOps Studio",
    description="AI-Native Healthcare Workflow & Microservice Generation Platform",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Middleware Stack ──────────────────────────────────────
# Order matters! Middleware runs top-to-bottom on request, bottom-to-top on response.
# 1. CORS (must be outermost for preflight requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
# 2. Security headers (on every response)
app.add_middleware(SecurityHeadersMiddleware)
# 3. Correlation ID (for request tracing)
app.add_middleware(CorrelationIdMiddleware)
# 4. Rate limiting (reject abusive requests early)
app.add_middleware(RateLimitMiddleware)
# 5. Request logging (structured JSON logs for every request)
app.add_middleware(RequestLoggingMiddleware)


# ── Routes ────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(workflows.router)
app.include_router(ai.router)
app.include_router(admin.router)
app.include_router(jobs.router)
app.include_router(datasets.router)


# ── Health Check ──────────────────────────────────────────
# Used by Docker, Kubernetes, and load balancers to verify the app is alive.
@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "healthops-studio"}
