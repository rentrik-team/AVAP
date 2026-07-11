from fastapi import APIRouter

from app.api.routes.v1 import targets, scans

api_router = APIRouter()

api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
