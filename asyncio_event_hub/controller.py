"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from contextlib import suppress, asynccontextmanager
from enum import Enum
from sys import _getframe
from typing import Any, List, Dict, Callable, TypeVar, Coroutine, Union, Optional


from .doc import doc_category

import asyncio
import warnings

T = TypeVar('T')
TEvent = Union[Enum, str, int]


__all__ = (
    "EventController",
)

@doc_category("Event reference")
class EventListener:
    """
    .. versionadded:: 1.0

    Represents a listener (handler) of an event.

    Attributes
    --------------
    fnc: Callable[[T], Any]
        The actual registered handler function.
    predicate: Optional[Callable[[T], bool]]
        Condition function that gets called before ``fnc`` and must return True, if the ``fnc``
        is to be called.
    """
    def __init__(self, fnc: Callable[[T], Any], predicate: Optional[Callable[[T], bool]] = None) -> None:
        self.fnc = fnc
        self.predicate = predicate

    def __eq__(self, o):
        return (isinstance(o, EventListener) and self.fnc is o.fnc) or o == self.fnc

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.fnc(*args, **kwds)

    def __hash__(self) -> int:
        return hash(self.fnc)


@doc_category("Event reference")
class EventController:
    """
    .. versionadded:: 1.0

    Responsible for controlling the event loop, listening and emitting events.
    """
    def __init__(self) -> None:
        self._listeners: Dict[TEvent, List[EventListener]] = {}
        self._current_waiting: int = None
        self._loop_task: asyncio.Task = None
        self._running = False
        self._subcontrollers: List[EventController] = []
        self._mutex = asyncio.Lock()  # Critical section lock
        self._priority_queues = None
        self.clear_queue()

    @property
    def running(self) -> bool:
        """
        .. versionadded:: 1.0

        Returns bool indicating if the controller is running or not.
        """
        return self._running

    @property
    def subcontrollers(self) -> List["EventController"]:
        """
        .. versionadded:: 1.0

        Returns a list of controller's sub-controllers.
        """
        return self._subcontrollers[:]

    @asynccontextmanager
    async def critical(self):
        """
        .. versionadded:: 1.0

        Method that returns an async context manager, that prevents any events from being processed
        while in the critical section.

        Example:

        .. code-block:: python

            async with controller.critical():
                # Can't process events here
                await something.initialize()

            # Can process events here
              
        """
        await self._mutex.acquire()
        yield
        self._mutex.release()

    def start(self):
        """
        .. versionadded:: 1.0

        Starts the event loop of this master controller and it's subcontrollers.
        """
        if not self._running:
            self.clear_queue()
            self._loop_task = asyncio.create_task(self.event_loop())
            self._running = True

            for controller in self._subcontrollers:  # Run subcontrollers
                if controller._running:
                    continue

                controller.start()

    def add_subcontroller(self, controller: "EventController"):
        """
        .. versionadded:: 1.0

        Adds a sub-controller, that also receives events emitted to the current controller.
        If this master controller is running and the ``controller`` being added is not, it is automatically
        started. If this master controller is not running, the ``controller`` being added is started,
        after this master controller is started.

        Parameters
        -----------
        controller: EventController
            The controller to add as a sub-controller.
        """
        if self._running and not controller._running:
            controller.start()

        self._subcontrollers.append(controller)

    def remove_subcontroller(self, controller: "EventController"):
        """
        .. versionadded:: 1.0

        Removes the sub-controller.
        The sub-controller IS NOT stopped.

        Parameters
        -----------
        controller: EventController
            The controller to remove.

        Raises
        ---------
        ValueError
            The ``controller`` is not a subcontroller of the current controller
        """
        self._subcontrollers.remove(controller)

    def stop(self):
        """
        .. versionadded:: 1.0

        Stops event loop asynchronously

        Returns
        ----------
        asyncio.Future
            A Future object that can be used to await for the controller's task to stop
            and also the tasks of all the subcontrollers.
        """
        if self._running:
            self.emit("__dummy_event__")
            self._running = False

        return asyncio.gather(self._loop_task, *(c.stop() for c in self._subcontrollers))

    def add_listener(self, event: TEvent, fnc: Callable[[T], Any], predicate: Optional[Callable[[T], bool]] = None):
        """
        .. versionadded:: 1.0

        Registers the function ``fnc`` as an event listener for ``event``.
        
        Parameters
        ------------
        event: Union[Enum, str, int]
            The event of listener to add.
        fnc: Callable
            The function listener to add.
        predicate: Optional[Callable[[Any], bool]]
            Optional function parameter that accepts the same parameters as ``fnc`` and must return
            True, indicating if ``fnc`` is to be called or not. If it returns False, the ``fnc`` does not
            get called after event is emitted.
        """
        listeners = self._listeners[event] = self._listeners.get(event, [])
        listeners.append(EventListener(fnc, predicate))

    def remove_listener(self, event: TEvent, fnc: Callable):
        """
        .. versionadded:: 1.0

        Remove the function ``fnc`` from the list of listeners for ``event``.

        Parameters
        ------------
        event: Union[Enum, str, int]
            The event of listener to remove.
        fnc: Callable
            The function listener to remove.

        Raises
        ---------
        KeyError
            The event doesn't have any listeners.
        ValueError
            Provided function is not a listener.
        """
        with suppress(ValueError, KeyError):
            self._listeners[event].remove(fnc)

    def listen(self, event: TEvent):
        """
        .. versionadded:: 1.0

        Decorator used to register the function as an event listener.

        Example:

        .. code-block:: python

            ctrl = EventController()

            @ctrl.listen("my_event")
            async def event_handler():
                print("Received event")

        Parameters
        ---------------
        event: Union[Enum, str, int]
            The event that needs to occur for the function to be called.
        """
        def _listen_decor(fnc: Callable):
            self.add_listener(event, fnc)
            return fnc

        return _listen_decor

    def emit(self, event: TEvent, *args, priority: int = 0, **kwargs) -> asyncio.Future:
        """
        .. versionadded:: 1.0

        Emits an ``event`` by calling all the registered listeners from the event loop.

        Example:

        .. code-block:: python

            ctrl = EventController()
            ... # Add listeners (handlers)
            ctrl.emit("my_event")

        Parameters
        -----------
        event: Union[Enum, str, int]
            The event to emit.
        args
            Variadic positional arguments passed to event listeners.
        priority: int
            .. versionadded:: 1.1

            The priority of event. Events with higher priority are
            processed before the ones with lower priority. Defaults to 0.
            This is a keyword only priority.
        kwargs
            Variadic keyword arguments passed to event listeners.

        Returns
        ---------
        asyncio.Future
            A future object that can be awaited.
            You can use this to wait for the event to actually be processed.
            The result of the future will always be None.

        Raises
        ---------
        TypeError
            Arguments provided don't match all the listener parameters.
        """
        future = asyncio.Future()
        if not self._running:
            future.set_result(None)
            caller_frame = _getframe(1)
            caller_info = caller_frame.f_code
            caller_text = f"{caller_info.co_name} ({caller_info.co_filename})"
            warnings.warn(
                f"{self} is not running, but {event} was emitted, which was ignored! Caller: {caller_text}",
                stacklevel=2
            )
            return future

        priority_queues = self._priority_queues
        queue = priority_queues.get(priority)
        if queue is None:
            priority_queues[priority] = queue = asyncio.Queue()
            self._priority_queues = {p: priority_queues[p] for p in sorted(priority_queues, reverse=True)}

        cw = self._current_waiting
        if cw is not None and cw < priority:
            self.emit("__dummy_event__", priority=cw)

        queue.put_nowait((event, args, kwargs, future))

        # Also emit and for sublisteners and create awaitable future that waits for all controllers
        # to emit the events and process.
        future = asyncio.gather(
            future,
            *[
                controller.emit(event, *args, **kwargs)
                for controller in self._subcontrollers
                if controller.running
            ]
        )  # Create a new future, that can be awaited for all event controllers to process an event

        return future
    
    def clear_queue(self):
        """
        .. versionadded:: 1.0

        Clears all emitted events from queue (recreates the queue).
        """
        self._priority_queues: Dict[int, asyncio.Queue] = {
            -1: asyncio.Queue()  # Dummy queue awaited when no other queues have anything to handle
        }


    async def event_loop(self):
        """
        .. versionadded:: 1.0

        Event loop task.
        """
        listeners = self._listeners

        event_id: TEvent
        future: asyncio.Future

        while self._running:
            for p, q in self._priority_queues.items():
                if q.empty():
                    continue

                break
            else:
                p = -1
                q = self._priority_queues[p]

            self._current_waiting = p
            event_id, args, kwargs, future = await q.get()
            self._current_waiting = None

            async with self.critical():
                for listener in listeners.get(event_id, [])[:]:
                    try:
                        if listener.predicate is None or listener.predicate(*args, **kwargs):
                            if isinstance(r:= listener(*args, **kwargs), Coroutine):
                                await r

                    except Exception as exc:
                        warnings.warn(f"({exc}) Could not call event handler {listener} for event {event_id}.")
                        future.set_exception(exc)
                        break


                if not future.done():  # In case exception was set
                    future.set_result(None)

        self.clear_queue()
