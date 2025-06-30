

import random

from fastapi import APIRouter

from app.schemas.results.top import RandomTop

router = APIRouter()
swim_styles = [
    {"stroke": "APNEA", "distance": 50},
    {"stroke": "BIFINS", "distance": 50},
    {"stroke": "BIFINS", "distance": 100},
    {"stroke": "BIFINS", "distance": 200},
    {"stroke": "BIFINS", "distance": 400},
    {"stroke": "IMMERSION", "distance": 100},
    {"stroke": "IMMERSION", "distance": 400},
    {"stroke": "SURFACE", "distance": 50},
    {"stroke": "SURFACE", "distance": 100},
    {"stroke": "SURFACE", "distance": 200},
    {"stroke": "SURFACE", "distance": 400},
    {"stroke": "SURFACE", "distance": 800},
    {"stroke": "SURFACE", "distance": 1500},
]


@router.get("/", response_model=RandomTop)
async def get_random_top():
    item = random.choice(swim_styles)
    return item
