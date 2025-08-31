from typing import List
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.query_utils import Prefetch
from tortoise.expressions import F, Case, When
from fastapi import APIRouter

from app.core.security.deps.user_auth import SessionAuthSecurity, UserAuthSecurity
from app.models.tokens.refresh_tokens import RefreshToken
from app.models.tokens.sessions import Session
from app.models.user.user import User
from app.schemas import with_nested

router = APIRouter(tags=['Me/Auth/Session'])

RefreshToken_Pydantic = pydantic_model_creator(RefreshToken)
Session_Pydantic = with_nested(pydantic_model_creator(Session),
                               refresh_tokens=List[RefreshToken_Pydantic],
                               is_current_session=bool)


@router.get("/")
async def get_sessions(
    user: User = UserAuthSecurity(),
    session: Session = SessionAuthSecurity()
):
    sessions = await Session_Pydantic.from_queryset(
        Session.filter(user_id=user.id, revoked_at__isnull=True)
        .annotate(
            is_current_session=Case(
                When(id=session.id, then='true'),
                default='false'
            )
        )
        .prefetch_related(
            Prefetch(
                "refresh_tokens",
                queryset=RefreshToken.all().order_by("-issued_at")
            )
        )
    )
    return sessions
