from fastapi import APIRouter

from .auth import auth_router
from .scenarios import scenarios_router
from .session import session_router

api_routers = APIRouter()
api_routers.include_router(auth_router)
api_routers.include_router(scenarios_router)
api_routers.include_router(session_router)
