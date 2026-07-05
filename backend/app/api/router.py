from fastapi import APIRouter

from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.profile.routes import router as profile_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(chat_router)
api_router.include_router(profile_router)
