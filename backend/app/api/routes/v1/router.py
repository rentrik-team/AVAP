from fastapi import APIRouter

from app.api.routes.v1.targets import router as targets_router

api_router = APIRouter()

api_router.include_router(targets_router, prefix="/targets", tags=["targets"])
