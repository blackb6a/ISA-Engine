from enum import Enum, auto
import functools


class EventType(Enum):
    EXIT = auto()
    STEP = auto()
    INPUT = auto()
    OUTPUT = auto()
    BREAKPOINT = auto()
    ERROR = auto()
    DOWNLOAD = auto()


class EventEmitter:
    def __init__(self):
        # Initialise a list of 'before/after' event handler
        self.__handlers = {
            "before": {},
            "after": {},
        }

    # Return a decorator that can trigger event handler.
    def emit(self, event_type: EventType) -> callable:
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                await self.trigger(event_type, "before", *args, **kwargs)
                result = await func(*args, **kwargs)
                await self.trigger(event_type, "after", *args, result, **kwargs)
                return result

            return wrapper

        return decorator

    # Add/Overwrite function from the list of handler.
    def add_handler(self, event_type: EventType, pos: str, func: callable):
        self.__handlers[pos][event_type] = func

    # Remove function from the list of handler.
    def remove_handler(self, event_type: EventType, pos: str):
        if event_type in self.__handlers[pos].keys():
            self.__handlers[pos].pop(event_type)

    # Trigger before/after event handler.
    async def trigger(self, event_type: EventType, pos: str, *args, **kwargs):
        if event_type in self.__handlers[pos].keys():
            handler = self.__handlers[pos][event_type]
            return await handler(*args, **kwargs)
