from datetime import datetime
from typing import List
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.query_utils import Prefetch
from tortoise.expressions import F, Case, When
from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
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

MIN_REVOKE_DELAY = 60 * 60 * 24  # 1 day


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
        .order_by("-created_at")
    )
    return sessions


@router.delete("/", status_code=204)
async def revoke_all_sessions(
    user: User = UserAuthSecurity(),
    session: Session = SessionAuthSecurity()
):
    now = datetime.now()
    if now.timestamp() - session.created_at.timestamp() < MIN_REVOKE_DELAY:
        raise APIError(ErrorCode.SESSION_REVOKE_COOLDOWN)

    sessions_to_revoke = await Session.filter(
        user_id=user.id,
        revoked_at__isnull=True,
        id__not=session.id
    ).all()

    if not sessions_to_revoke:
        return

    for s in sessions_to_revoke:
        s.revoked_at = now
    await Session.bulk_update(sessions_to_revoke, fields=["revoked_at"])

    session_ids = [s.id for s in sessions_to_revoke]
    await RefreshToken.filter(session_id__in=session_ids, revoked_at__isnull=True).update(revoked_at=now)


@router.delete("/{id}", status_code=204)
async def revoke_session(
    id: int,
    user: User = UserAuthSecurity(),
    session: Session = SessionAuthSecurity(),
):
    now = datetime.now()
    if now.timestamp() - session.created_at.timestamp() < MIN_REVOKE_DELAY:
        raise APIError(ErrorCode.SESSION_REVOKE_COOLDOWN)

    if id == session.id:
        raise APIError(ErrorCode.SESSION_SELF_REVOKE)

    session_del = await Session.get_or_none(id=id)
    if not session_del or session_del.user_id != user.id:
        raise APIError(ErrorCode.SESSION_NOT_FOUND)

    session_del.revoked_at = now
    await session_del.save()
    await RefreshToken.filter(session=session_del, revoked_at__isnull=True).update(revoked_at=now)
