import importlib.util
import os
from pathlib import Path

from fastapi import FastAPI

ROUTES_DIR = Path(os.getcwd()) / 'app' / 'pages'


def path_from_dir(route_dir: Path) -> str:
    relative = route_dir.relative_to(ROUTES_DIR)
    parts = list(relative.parts)

    cleaned = []
    for part in parts:
        if part.startswith('(') and part.endswith(')'):
            continue
        elif part.startswith('[') and part.endswith(']'):
            cleaned.append("{" + part[1:-1] + "}")
        else:
            cleaned.append(part)

    return "/" + "/".join(cleaned)


def import_router_from_file(route_file: Path):
    spec = importlib.util.spec_from_file_location("route_module", route_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "router", None)


def include_routes(app: FastAPI):
    for route_dir in ROUTES_DIR.rglob("*"):
        route_file = route_dir / "route.py"
        if route_file.exists():
            prefix = path_from_dir(route_dir)
            router = import_router_from_file(route_file)

            if router:
                relative = route_dir.relative_to(ROUTES_DIR)
                tag_parts = [
                    part for part in relative.parts
                    if not (part.startswith('(') and part.endswith(')'))
                ]
                tag = tag_parts[0] if tag_parts else None

                app.include_router(router, prefix=prefix, tags=[tag])
