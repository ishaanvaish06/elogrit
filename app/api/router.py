from fastapi import APIRouter

from app.api.routes.contests import router as contests_router
from app.api.routes.users import router as users_router
from app.api.routes.llm import router as llm_router

api_router = APIRouter(prefix="/api/v1/leetcode")

api_router.include_router(contests_router)
api_router.include_router(users_router)
api_router.include_router(llm_router)
