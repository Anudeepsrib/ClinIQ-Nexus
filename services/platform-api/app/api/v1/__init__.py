from fastapi import APIRouter

from . import admin, auth, chat, documents, patients, workflows, reviews, audit, memory

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(patients.router, prefix="/patients", tags=["Patients"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(chat.router, prefix="/ai", tags=["AI"])
router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
router.include_router(reviews.router, prefix="/reviews", tags=["Human Review"])
router.include_router(audit.router, prefix="/audit", tags=["Audit"])
router.include_router(memory.router, prefix="/memory", tags=["Hindsight Memory"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
