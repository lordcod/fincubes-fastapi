from fastapi import APIRouter, Response
from app.shared.utils.scopes.request import require_scope
from app.shared.utils.sitemap import generate_sitemap

router = APIRouter(tags=['Public/Client/Sitemap'])


@router.get("/", response_class=Response)
@require_scope('sitemap:read')
async def get_sitemap():
    xml_bytes = await generate_sitemap()

    return Response(
        content=xml_bytes,
        media_type="application/xml; charset=utf-8",
        headers={
            "Cache-Control": "public, s-maxage=3600, stale-while-revalidate=59"
        },
    )
