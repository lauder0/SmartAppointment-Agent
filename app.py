"""FastAPI entrypoint for Smart Appointment Agent 3.0."""

from typing import List, Optional
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api import api_routers
from api.core.exceptions import BusinessException, api_exception_handler, general_exception_handler
from services.knowledge_service import KnowledgeService
from services.recommendation_service import RecommendationService
from services.service_catalog_service import ServiceCatalogService
from services.technician_service import TechnicianService
from web import router as web_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeRequest(BaseModel):
    content: str
    category: str
    keywords: List[str] = []


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None


async def initialize_system():
    """Initialize local knowledge, technician, service, and recommendation services."""
    try:
        logger.info("Initializing Smart Appointment Agent 3.0...")

        logger.info("Initializing knowledge service...")
        knowledge_service = KnowledgeService()
        await knowledge_service.initialize()

        logger.info("Initializing technician service...")
        technician_service = TechnicianService()
        technician_service.initialize_default_technicians()

        logger.info("Initializing service catalog...")
        service_catalog_service = ServiceCatalogService()
        service_catalog_service.initialize_default_services()

        logger.info("Starting recommendation scheduler...")
        recommendation_service = RecommendationService()
        if recommendation_service.start_scheduler():
            logger.info("Recommendation scheduler started")
        else:
            logger.warning("Recommendation scheduler did not start")

        logger.info("Smart Appointment Agent 3.0 initialization complete")

    except Exception:
        logger.exception("Smart Appointment Agent 3.0 initialization failed")
        raise


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title="Smart Appointment Agent 3.0",
        description=(
            "Supervisor + specialist subgraph appointment assistant with consultation, "
            "availability, booking, and recommendation domains."
        ),
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(BusinessException, api_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    for router in api_routers:
        app.include_router(router)

    app.include_router(web_router)
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

    @app.on_event("startup")
    async def startup_event():
        await initialize_system()

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
