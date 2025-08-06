from fastapi import APIRouter, Depends
from app.core.protection.secure_request import SecureRequest

router = APIRouter(dependencies=[Depends(SecureRequest())])
