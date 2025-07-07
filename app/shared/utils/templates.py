from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(loader=FileSystemLoader("app/templates/"),
                  autoescape=select_autoescape())


def get_template(name: str, context: Optional[dict] = None, **kwargs):
    template = env.get_template(name)
    if context is not None:
        kwargs.update(context)
    return template.render(**kwargs)
