from fastapi import APIRouter, Depends

from app.core.security.deps.scope_auth import ScopeAuthSecurity


router = APIRouter(dependencies=[ScopeAuthSecurity()])
