from fastapi import APIRouter
from app.core.security.deps.scope_auth import ScopeAuthSecurity


router = APIRouter(dependencies=[ScopeAuthSecurity()])
