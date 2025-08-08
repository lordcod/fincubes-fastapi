import inspect
from typing import Callable, Awaitable, Any, Dict, List, Optional, ParamSpec, TypeVar

TEvent = TypeVar("TEvent")
P = ParamSpec("P")
MiddlewareCallable = Callable[
    P,
    Awaitable[Optional[Dict[str, Any]]]
]


class MiddlewareManager:
    def __init__(self):
        self.middlewares: List[MiddlewareCallable] = []

    def register(self, middleware: MiddlewareCallable):
        self.middlewares.append(middleware)

    def extract_kwargs(self, handler, data):
        sig = inspect.signature(handler)
        kwargs = {
            k: data[k] for k in sig.parameters if k in data
        }
        return kwargs

    async def run(
        self,
        handler: Optional[Callable[..., Awaitable[Any]]] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ):
        data = initial_data.copy() if initial_data is not None else {}
        handlers = self.middlewares.copy()
        if handler:
            handlers.append(handler)

        for mh in handlers:
            kwargs = self.extract_kwargs(mh, data)
            payload = await mh(**kwargs)
            if payload is not None:
                data.update(payload)
