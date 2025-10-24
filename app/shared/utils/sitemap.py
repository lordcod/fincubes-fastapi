import datetime
import xml.etree.ElementTree as ET
from app.repositories.sitemap import get_athletes_last_update, get_competitions_last_update
from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.clients.redis import client


def create_element(tag: str, text: str) -> ET.Element:
    el = ET.Element(tag)
    el.text = text
    return el


def create_url_element(loc, lastmod, changefreq=None, priority=None):
    url_el = ET.Element("url")
    url_el.append(create_element("loc", loc))
    url_el.append(create_element("lastmod", lastmod))
    if changefreq:
        url_el.append(create_element("changefreq", changefreq))
    if priority:
        url_el.append(create_element("priority", priority))
    return url_el


async def _generate_sitemap_static() -> bytes:
    """
    Асинхронно создаёт sitemap.xml, используя SQL-запросы через Tortoise.
    """
    urlset = ET.Element(
        "urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    static_pages = [
        ("https://fincubes.ru/", today_str, "daily", "1.0"),
        ("https://fincubes.ru/top", today_str, "daily", "1.0"),
        ("https://fincubes.ru/standards", today_str, "daily", "1.0"),
        ("https://fincubes.ru/records", today_str, "daily", "1.0"),
        ("https://fincubes.ru/region", today_str, "daily", "1.0"),
        ("https://fincubes.ru/event", today_str, "daily", "1.0"),
        ("https://fincubes.ru/team", today_str, "daily", "0.8"),
        ("https://fincubes.ru/about", today_str, "daily", "0.8"),
        ("https://fincubes.ru/privacy", today_str, "daily", "0.8"),
        ("https://fincubes.ru/terms", today_str, "daily", "0.8"),
        ("https://fincubes.ru/login", today_str, "daily", "0.8"),
        ("https://fincubes.ru/signup", today_str, "daily", "0.8"),
    ]
    for loc, lastmod, cf, pr in static_pages:
        urlset.append(create_url_element(loc, lastmod, cf, pr))

    competitions = await get_competitions_last_update()
    for comp in competitions:
        lastmod = comp["last_update"]
        urlset.append(create_url_element(
            f"https://fincubes.ru/event/{comp['id']}",
            lastmod.strftime("%Y-%m-%d"),
            "monthly",
            "0.7"
        ))

    athletes = await get_athletes_last_update()
    for ath in athletes:
        lastmod = ath["last_update"]
        urlset.append(create_url_element(
            f"https://fincubes.ru/user/{ath['id']}",
            lastmod.strftime("%Y-%m-%d"),
            "weekly",
            "0.5"
        ))

    xml_bytes = ET.tostring(urlset, encoding="utf-8", xml_declaration=True)
    return xml_bytes


async def generate_sitemap() -> bytes:
    cache = RedisCachePickleCompressed(client)
    cache_key = "sitemap"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    result = await _generate_sitemap_static()
    await cache.set(cache_key, result, expire_seconds=60 * 60)
    return result
