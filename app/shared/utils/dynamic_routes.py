import importlib.util
import os
from pathlib import Path

from fastapi import APIRouter, FastAPI

ROUTES_DIR = Path(os.getcwd()) / 'app' / 'pages_v2'


def path_from_dir(relative: Path) -> str:
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


def build_router_tree(route_dir: Path) -> APIRouter:
    route_path = route_dir / "route.py"
    router = import_router_from_file(
        route_path) if route_path.exists() else None
    if router is None:
        router = APIRouter()

    for sub_dir in route_dir.iterdir():
        if sub_dir.is_dir():
            sub_router = build_router_tree(sub_dir)
            prefix = path_from_dir(sub_dir.relative_to(route_dir))
            router.include_router(sub_router, prefix=prefix)

    return router


def include_routes(app: FastAPI):
    root_router = build_router_tree(ROUTES_DIR)
    app.include_router(root_router)
