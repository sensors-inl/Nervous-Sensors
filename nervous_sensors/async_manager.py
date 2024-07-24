import asyncio
from abc import ABC


class AsyncManager(ABC):
    def __init__(self):
        self._stop_event = asyncio.Event()

    async def start(self):
        pass

    async def stop(self):
        pass
