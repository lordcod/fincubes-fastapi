from fastapi import APIRouter

from . import coach
from . import parent

router = APIRouter(prefix="/users")

router.include_router(parent.router)
router.include_router(coach.router)
