from fastapi import APIRouter, Body
from app.core.security.deps.base_auth import BaseDecodeToken, CheckTokenType
from app.core.security.schema import TokenType
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post("/", response_model=dict)
@require_scope('token:.payload:get')
async def get_token_payload(token: str = Body(embed=True)):
    payload = BaseDecodeToken().decode_token(token)
    CheckTokenType(TokenType.access).check_payload(payload)
    return payload
