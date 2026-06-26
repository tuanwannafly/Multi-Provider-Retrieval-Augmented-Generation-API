import logging

from fastapi import FastAPI

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-LLM RAG API",
    description="Multi-Provider Retrieval-Augmented Generation API",
    version=settings.app_version,
)


@app.get("/")
async def root():
    return {"name": "Multi-LLM RAG API", "version": settings.app_version}
