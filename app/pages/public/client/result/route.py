
from typing import List, Optional

from fastapi import APIRouter, Depends

from app.core.protection.secure_request import SecureRequest
from app.models.competition.result import Result
from app.schemas.results.result import Result_Pydantic

router = APIRouter(tags=['Public/Client/Results'])


@router.get("/",
            response_model=List[Result_Pydantic],
            dependencies=[Depends(SecureRequest())])
async def get_results(
    competition_id: int,
    stroke: str,
    distance: int,
    gender: str,
):
    filters = {}
    if competition_id:
        filters["competition_id"] = competition_id
    if gender:
        filters["athlete__gender"] = gender
    if stroke:
        filters["stroke"] = stroke
    if distance:
        filters["distance"] = distance

    query = Result.filter(**filters)
    return await Result_Pydantic.from_queryset(query)

# async def get_results(
#     athlete_id: Optional[int] = None,
#     competition_id: Optional[int] = None,
#     stroke: Optional[str] = None,
#     distance: Optional[int] = None,
#     gender: Optional[str] = None,
# ):
#     filters = {}
#     if athlete_id:
#         filters["athlete_id"] = athlete_id
#     if competition_id:
#         filters["competition_id"] = competition_id
#     if gender:
#         filters["athlete__gender"] = gender
#     if stroke:
#         filters["stroke"] = stroke
#     if distance:
#         filters["distance"] = distance

#     query = Result.filter(**filters)
#     return await Result_Pydantic.from_queryset(query)
