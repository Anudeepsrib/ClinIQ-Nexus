"""Startup utilities (migrations + seeding for local dev)."""

import asyncio
import subprocess
import sys
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


async def run_migrations():
    """Run alembic migrations (used in docker-compose for local dev)."""
    logger.info("running_alembic_migrations")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.error("alembic_failed", stderr=result.stderr)
        else:
            logger.info("alembic_migrations_complete")
    except Exception as e:
        logger.exception("migration_error", error=str(e))


async def seed_if_dev():
    """Seed demo data only in development."""
    from app.core.config import settings
    if settings.ENVIRONMENT != "development":
        return
    try:
        from scripts.seed_demo_data import seed
        await seed()
    except Exception as e:
        logger.warning("seed_failed_or_skipped", error=str(e))
