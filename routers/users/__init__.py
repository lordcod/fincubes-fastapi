from fastapi import APIRouter

from . import athletes
from . import coaches
from . import parent

router = APIRouter(prefix="/users", tags=['users'])

router.include_router(parent.router)
router.include_router(coaches.router)
router.include_router(athletes.router)
