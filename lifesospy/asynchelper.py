"""
This module contains the AsyncHelper class.
"""

import asyncio
import logging

from typing import Callable, Any

_LOGGER = logging.getLogger(__name__)


class AsyncHelper(object):
    """Helper to create, track and cancel tasks."""

    def __init__(self):
        self._loop = asyncio.get_event_loop()
        self._pending_tasks = []

    def create_task(self, target: Callable[..., Any], *args: Any)\
            -> asyncio.tasks.Task:
        """Create task and add to our collection of pending tasks."""
        if asyncio.iscoroutine(target):
            task = self._loop.create_task(target)
        elif asyncio.iscoroutinefunction(target):
            task = self._loop.create_task(target(*args))
        else:
            raise ValueError("Expected coroutine as target")
        self._pending_tasks.append(task)
        return task

    def cancel_pending_tasks(self):
        """Cancel all pending tasks."""
        for task in self._pending_tasks:
            task.cancel()
            if not self._loop.is_running():
                try:
                    self._loop.run_until_complete(task)
                except asyncio.CancelledError:
                    pass
                except Exception: # pylint: disable=broad-except
                    _LOGGER.error("Unhandled exception from async task",
                                  exc_info=True)
