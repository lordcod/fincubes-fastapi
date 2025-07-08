from fastapi import APIRouter

from app.core.security.deps.bot_auth import BotAuthSecurity

router = APIRouter(dependencies=[BotAuthSecurity()])
