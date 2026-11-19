"""
InfraSphere AI — Unified AI Infrastructure Operating Platform.
Main FastAPI Application Entrypoint.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agentops import router as agentops_router
from app.api.approvals import router as approvals_router
from app.api.assets import router as assets_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.data_sources import router as data_sources_router
from app.api.health import router as health_router
from app.api.incidents import router as incidents_router
from app.api.knowledge import router as knowledge_router
from app.api.metrics import router as metrics_router
from app.api.secureai import router as secureai_router
from app.api.users import router as users_router
from app.api.workforce import router as workforce_router
from app.config import settings
from app.core.database import AsyncSessionLocal, create_tables
from app.core.exceptions import register_exception_handlers
from app.seed.demo_data import seed_all_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("infrasphere")


# ---------------------------------------------------------------------------
# WebSocket Manager for Live Telemetry
# ---------------------------------------------------------------------------
class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket: {e}")
                self.disconnect(connection)


ws_manager = WebSocketConnectionManager()


# ---------------------------------------------------------------------------
# Lifespan Handler: Table Creation & Demo Seeding
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing InfraSphere AI backend...")
    # 1. Create tables
    await create_tables()
    logger.info("Database schema verified.")

    # 2. Seed demo dataset if enabled
    if settings.enable_demo_data:
        async with AsyncSessionLocal() as session:
            try:
                await seed_all_data(session)
            except Exception as e:
                logger.error(f"Error seeding demo data: {e}", exc_info=True)

    logger.info("InfraSphere AI operational and ready for requests.")
    yield
    logger.info("InfraSphere AI shutting down.")


# ---------------------------------------------------------------------------
# FastAPI App Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="The Intelligent Operating System for Trusted AI — Bangladesh Infrastructure Intelligence & Response Platform",
    lifespan=lifespan,
)

# Exception handlers
register_exception_handlers(app)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Include All Routers under /api/v1
# ---------------------------------------------------------------------------
prefix = settings.api_prefix

app.include_router(auth_router, prefix=prefix)
app.include_router(users_router, prefix=prefix)
app.include_router(incidents_router, prefix=prefix)
app.include_router(assets_router, prefix=prefix)
app.include_router(secureai_router, prefix=prefix)
app.include_router(knowledge_router, prefix=prefix)
app.include_router(workforce_router, prefix=prefix)
app.include_router(agentops_router, prefix=prefix)
app.include_router(approvals_router, prefix=prefix)
app.include_router(audit_router, prefix=prefix)
app.include_router(metrics_router, prefix=prefix)
app.include_router(data_sources_router, prefix=prefix)
app.include_router(health_router, prefix=prefix)


# ---------------------------------------------------------------------------
# WebSocket Endpoint for Live Telemetry
# ---------------------------------------------------------------------------
@app.websocket("/ws/operations")
async def websocket_operations_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        # Send initial handshake
        await websocket.send_json({
            "event": "connected",
            "message": "Connected to InfraSphere AI real-time operations feed",
        })
        while True:
            # Keep connection open and receive optional ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket session terminated: {e}")
        ws_manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Root Info Endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["system"])
async def root_info():
    return {
        "app": settings.app_name,
        "tagline": "The Intelligent Operating System for Trusted AI",
        "flagship": "InfraOps BD — Bangladesh Infrastructure Intelligence & Response",
        "version": settings.version,
        "docs_url": "/docs",
        "api_prefix": settings.api_prefix,
        "pillars": [
            "SecureAI",
            "WorkforceOS",
            "Knowledge Grid",
            "AgentOps",
            "Human+AI",
        ],
        "status": "operational",
    }
