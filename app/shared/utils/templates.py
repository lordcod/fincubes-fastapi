from pathlib import Path
from typing import Optional
import anyio
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT_PATH = Path('app/')
SQL_PATH_FOLDER = ROOT_PATH / 'sql'
TEMPLATES_PATH_FOLDER = ROOT_PATH / 'templates'
env = Environment(loader=FileSystemLoader(TEMPLATES_PATH_FOLDER),
                  autoescape=select_autoescape(),
                  enable_async=True)


async def get_template(name: str, context: Optional[dict] = None, **kwargs):
    template = env.get_template(name)
    if context is not None:
        kwargs.update(context)
    return await template.render_async(**kwargs)


async def get_sql(filename: str) -> str:
    async with await anyio.open_file(SQL_PATH_FOLDER / filename, mode='r') as f:
        return await f.read()
