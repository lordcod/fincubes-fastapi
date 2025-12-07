from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT_PATH = Path('app/')
TEMPLATES_PATH_FOLDER = ROOT_PATH / 'templates'
env = Environment(loader=FileSystemLoader(TEMPLATES_PATH_FOLDER),
                  autoescape=select_autoescape(),
                  enable_async=True)


async def get_template(name: str, context: Optional[dict] = None, **kwargs):
    template = env.get_template(name)
    if context is not None:
        kwargs.update(context)
    return await template.render_async(**kwargs)
