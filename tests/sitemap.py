import asyncio
import datetime
import typer
import xml.etree.ElementTree as ET
from typing import Optional

from tortoise import Tortoise
from app.core.config import settings
from app.models import Competition, Athlete

app = typer.Typer()


def create_element(tag: str, text: str) -> ET.Element:
    el = ET.Element(tag)
    el.text = text
    return el


def create_url_element(
    loc: str,
    lastmod: str,
    changefreq: Optional[str] = None,
    priority: Optional[str] = None
) -> ET.Element:
    url_el = ET.Element('url')
    url_el.append(create_element('loc', loc))
    url_el.append(create_element('lastmod', lastmod))
    if changefreq:
        url_el.append(create_element('changefreq', changefreq))
    if priority:
        url_el.append(create_element('priority', priority))
    return url_el


async def get_competition_last_update(comp: Competition) -> datetime.date:
    max_date = comp.updated_at.date()
    if hasattr(comp, 'results'):
        results = await comp.results
        for r in results:
            if r.updated_at.date() > max_date:
                max_date = r.updated_at.date()
    return max_date


async def get_athlete_last_update(athl: Athlete) -> datetime.date:
    max_date = athl.updated_at.date()
    if hasattr(athl, 'results'):
        results = await athl.results
        for r in results:
            if r.updated_at.date() > max_date:
                max_date = r.updated_at.date()
    return max_date


@app.command()
def generate() -> None:
    async def _generate_sitemap() -> None:
        await Tortoise.init(db_url=settings.DATABASE_URL, modules={"models": ["app.models"]})
        await Tortoise.generate_schemas()

        urlset = ET.Element(
            'urlset',
            xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        )
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        static_pages = [
            ('https://fincubes.ru/', today_str, 'daily', '1.0'),
            ('https://fincubes.ru/top', today_str, 'daily', '1.0'),
            ('https://fincubes.ru/standards', today_str, 'daily', '1.0'),
            ('https://fincubes.ru/records', today_str, 'daily', '1.0'),
            ('https://fincubes.ru/region', today_str, 'daily', '1.0'),
            ('https://fincubes.ru/event', today_str, 'daily', '1.0'),
            ('https://fincubes.ru/team', today_str, 'daily', '0.8'),
            ('https://fincubes.ru/about', today_str, 'daily', '0.8'),
            ('https://fincubes.ru/privacy', today_str, 'daily', '0.8'),
            ('https://fincubes.ru/terms', today_str, 'daily', '0.8'),
            ('https://fincubes.ru/login', today_str, 'daily', '0.8'),
            ('https://fincubes.ru/signup', today_str, 'daily', '0.8'),
        ]
        for loc, lastmod, changefreq, priority in static_pages:
            urlset.append(create_url_element(
                loc, lastmod, changefreq, priority))

        print('Загружаем соревнования...')
        competitions = await Competition.all().prefetch_related('results')
        for comp in competitions:
            last_update = await get_competition_last_update(comp)
            urlset.append(create_url_element(
                f'https://fincubes.ru/event/{comp.id}',
                last_update.strftime('%Y-%m-%d'),
                'monthly',
                '0.7'
            ))

        print('Загружаем спортсменов...')
        athletes = await Athlete.all().prefetch_related('results')
        for athl in athletes:
            last_update = await get_athlete_last_update(athl)
            urlset.append(create_url_element(
                f'https://fincubes.ru/user/{athl.id}',
                last_update.strftime('%Y-%m-%d'),
                'weekly',
                '0.5'
            ))

        xml_bytes = ET.tostring(urlset, encoding='utf-8', xml_declaration=True)
        with open('sitemap.xml', 'wb') as f:
            f.write(xml_bytes)

        print('sitemap.xml сгенерирован.')

        await Tortoise.close_connections()

    asyncio.run(_generate_sitemap())


if __name__ == '__main__':
    app()
