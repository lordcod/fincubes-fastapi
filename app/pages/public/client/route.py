from datetime import datetime
import hashlib
from urllib.parse import urlparse
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi import APIRouter, Depends
from app.core.protection.secure_request import SecureRequest

router = APIRouter()
