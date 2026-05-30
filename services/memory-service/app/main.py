"""Standalone FastAPI application for governed Hindsight Memory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="MediCore Hindsight Memory Service",
    version="0.1.0",
    description="Governed long-term memory for non-clinical workflow continuity.",
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "memory-service"}

