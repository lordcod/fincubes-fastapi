import asyncio
import inspect
from typing import Callable, Awaitable, Any, Dict, Generic, List, TypeVar

TEvent = TypeVar("TEvent")

MiddlewareCallable = Callable[
    [Callable[[TEvent, Dict[str, Any]], Awaitable[Any]], TEvent, Dict[str, Any]],
    Awaitable[Any]
]


class MiddlewareManager:
    def __init__(self):
        self.middlewares: List[MiddlewareCallable] = []

    def register(self, middleware: MiddlewareCallable):
        self.middlewares.append(middleware)

    async def _call_with_chain(
        self,
        index: int,
        handler: Callable[[TEvent, Dict[str, Any]], Awaitable[Any]],
        event: TEvent,
        data: Dict[str, Any]
    ) -> Any:
        if index < len(self.middlewares):
            mw = self.middlewares[index]

            async def next_handler(evt: TEvent, d: Dict[str, Any]):
                return await self._call_with_chain(index + 1, handler, evt, d)

            kwargs = self.extract_kwargs(mw, data)
            return await mw(next_handler, event, data, **kwargs)
        else:
            kwargs = self.extract_kwargs(handler, data)
            return await handler(event, **kwargs)

    def extract_kwargs(self, handler, data):
        sig = inspect.signature(handler)
        kwargs = {
            k: data[k] for k in sig.parameters if k in data
        }
        return kwargs

    async def run(
        self,
        handler: Callable[[TEvent, Any], Awaitable[Any]],
        event: TEvent,
        initial_data: Dict[str, Any] = None
    ):
        data = dict(initial_data or {})
        return await self._call_with_chain(0, handler, event, data)
