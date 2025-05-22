from fastapi import APIRouter

from . import athletes
from . import coach
from . import parent

router = APIRouter(prefix="/users", tags=['users'])

router.include_router(parent.router)
router.include_router(coach.router)
router.include_router(athletes.router)
