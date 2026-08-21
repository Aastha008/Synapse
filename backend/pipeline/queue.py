import asyncio
from typing import Callable, Any
from pydantic import BaseModel
from config import QUEUE_MAX_SIZE

class EventQueue:
    def __init__(self, max_size: int = QUEUE_MAX_SIZE):
        self._queues: dict[str, asyncio.Queue] = {}
        self._handlers: dict[str, list[Callable]] = {}
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._max_size = max_size
    
    async def publish(self, event_type: str, data: BaseModel | dict) -> None:
        if event_type not in self._queues:
            self._queues[event_type] = asyncio.Queue(maxsize=self._max_size)
        
        payload = data.model_dump() if isinstance(data, BaseModel) else data
        await self._queues[event_type].put(payload)
    
    async def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        if event_type not in self._queues:
            self._queues[event_type] = asyncio.Queue(maxsize=self._max_size)
    
    async def start(self) -> None:
        self._running = True
        for event_type, queue in self._queues.items():
            task = asyncio.create_task(self._consume(event_type, queue))
            self._tasks.append(task)
    
    async def _consume(self, event_type: str, queue: asyncio.Queue) -> None:
        while self._running:
            try:
                data = await queue.get()
                handlers = self._handlers.get(event_type, [])
                for handler in handlers:
                    try:
                        await handler(data)
                    except Exception as e:
                        print(f"Handler error for {event_type}: {e}")
                queue.task_done()
            except asyncio.CancelledError:
                break
    
    async def stop(self) -> None:
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
