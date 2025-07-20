import asyncio
import xml.etree.ElementTree as ET
import datetime
import email.utils
from tortoise import Tortoise
from app.models import Competition  # Импорт модели
from typing import Optional


def datetime_to_rfc822(dt: datetime.datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return email.utils.format_datetime(dt)


def create_element(name: str, text: Optional[str], ns: Optional[str] = None) -> ET.Element:
    ns_map = {
        'yandex': "http://news.yandex.ru",
        'media': "http://search.yahoo.com/mrss/",
        'content': "http://purl.org/rss/1.0/modules/content/",
    }
    if ns:
        tag = f"{{{ns_map[ns]}}}{name}"
    else:
        tag = name
    el = ET.Element(tag)
    el.text = text or ''
    return el


def format_competition_date(start: datetime.date, end: datetime.date) -> str:
    if start == end:
        return start.strftime('%d %B %Y')
    else:
        return f"{start.strftime('%d %B %Y')} — {end.strftime('%d %B %Y')}"


def generate_competition_description(comp: Competition) -> str:
    date_str = format_competition_date(comp.start_date, comp.end_date)
    city_str = f", г. {comp.city}" if comp.city else ""
    status_str = f"<p><strong>Статус:</strong> {comp.status}</p>" if comp.status else ""
    links_str = ""
    if comp.links:
        for data in comp.links:
            href = data.get("href", "#")
            title = data.get("title", "No Title")
            links_str += f'<p><a href="{href}">{title}</a></p>'

    description = (
        f"<p><strong>{comp.name}</strong></p>"
        f"<p><strong>Дата проведения:</strong> {date_str}</p>"
        f"<p><strong>Место:</strong> {comp.location}{city_str}</p>"
        f"<p><strong>Организатор:</strong> {comp.organizer}</p>"
        f"{status_str}"
        f"{links_str}"
    )
    return description


async def generate_rss() -> None:
    rss = ET.Element('rss', {
        'version': '2.0',
        'xmlns:yandex': "http://news.yandex.ru",
        'xmlns:media': "http://search.yahoo.com/mrss/",
        'xmlns:content': "http://purl.org/rss/1.0/modules/content/",
    })

    channel = ET.SubElement(rss, 'channel')
    channel.append(create_element(
        'title', 'Соревнования по подводному спорту'))
    channel.append(create_element('link', 'http://fincubes.ru/event/'))
    channel.append(create_element(
        'description', 'Статистика всех соревнований по подводному спорту'))
    channel.append(create_element('language', 'ru-RU'))
    channel.append(create_element('lastBuildDate',
                   datetime_to_rfc822(datetime.datetime.utcnow())))
    channel.append(create_element('generator', 'Custom Python RSS Generator'))

    print('Load events')
    competitions = await Competition.all().order_by('-updated_at')

    for comp in competitions:
        item = ET.SubElement(channel, 'item')
        item.append(create_element('title', comp.name))
        item.append(create_element(
            'link', f"https://fincubes.ru/event/{comp.id}"))
        item.append(create_element('author', comp.organizer))
        item.append(create_element('category', "Соревнования"))
        item.append(create_element(
            'pubDate', datetime_to_rfc822(comp.updated_at)))

        description_text = generate_competition_description(comp)
        item.append(create_element('description', description_text))
        # Просто вставляем описание без CDATA, чтобы XML был валидным
        item.append(create_element('encoded', description_text, ns='content'))

    xml_bytes = ET.tostring(rss, encoding='utf-8', xml_declaration=True)

    import xml.dom.minidom
    dom = xml.dom.minidom.parseString(xml_bytes)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')

    with open('rss.xml', 'wb') as f:
        f.write(pretty_xml)


async def main():
    from app.core.config import settings

    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]},
    )
    await Tortoise.generate_schemas()

    try:
        await generate_rss()
    finally:
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
