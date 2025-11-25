"""Lightweight in-process event bus for demo CQRS+EDA.

This provides a tiny publish/subscribe API used by command handlers
to emit domain events and by projections to update read models.
"""
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._subs = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        """Subscribe a handler to an event type string."""
        self._subs[event_type].append(handler)

    def publish(self, event_type: str, payload: Any):
        """Publish an event to all subscribers for event_type.

        Handlers are invoked synchronously in this simple implementation.
       """
        handlers = list(self._subs.get(event_type, []))
        for h in handlers:
            try:
                h(payload)
            except Exception as e:
                # keep bus robust: log and continue
                try:
                    print(f"[EventBus] handler error for {event_type}: {e}")
                except Exception:
                    pass


# single global bus instance for in-process usage
bus = EventBus()
