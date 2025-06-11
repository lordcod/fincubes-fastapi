from fastapi import APIRouter

from . import admin, auth, profile, verify

router = APIRouter(prefix="/users", tags=["auth"])

router.include_router(admin.router)
router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(verify.router)
