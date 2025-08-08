import random
import logging
from datetime import date, datetime

from fastapi import APIRouter

from app.models.competition.result import Result
from app.schemas.results.top import RandomTop
from app.shared.utils.scopes.request import require_scope
from app.shared.utils.metadata import COMBINATIONS

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=RandomTop)
@require_scope('top.random:read')
async def get_random_top():
    current_year = datetime.now().year
    combinations = COMBINATIONS.copy()
    random.shuffle(combinations)

    for style, gender, category in combinations:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Trying combination: style=%s, gender=%s, category=%s",
                style, gender, category
            )

        max_age = category.get("max_age")
        min_age = category.get("min_age")

        filters = {**style}
        if max_age is not None:
            filters["athlete__birth_year__gte"] = current_year - max_age
        if min_age is not None:
            filters["athlete__birth_year__lte"] = current_year - min_age

        today = date.today()
        season_year = current_year if today.month >= 9 else current_year - 1

        filters["competition__start_date__gte"] = date(season_year, 9, 1)
        filters["competition__start_date__lte"] = date(season_year + 1, 8, 31)
        filters["athlete__gender"] = gender

        results = await Result.filter(**filters)

        if len(results) >= 3:
            logger.info(
                "Results found for combination: style=%s, gender=%s, category=%s",
                style, gender, category
            )
            return RandomTop(
                **style,
                gender=gender,
                category=category,
            )
