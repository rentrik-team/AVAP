from fastapi import APIRouter

from app.api.routes.v1 import ai, assets, reports, risk, scans, targets, vulnerabilities

api_router = APIRouter()

api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["vulnerabilities"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
