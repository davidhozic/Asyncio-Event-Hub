"""
Module used to support listening and emitting events.
It also contains the event loop definitions.
"""
from contextlib import suppress, asynccontextmanager
from enum import Enum
from sys import _getframe
from typing import Any, List, Dict, Callable, TypeVar, Coroutine, Union


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
    def __init__(self, fnc: Callable, predicate: Callable[[T], bool] = None) -> None:
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
    Responsible for controlling the event loop, listening and emitting events.
    """
    def __init__(self) -> None:
        self._listeners: Dict[TEvent, List[EventListener]] = {}
        self._event_queue = asyncio.Queue()
        self._loop_task: asyncio.Task = None
        self._running = False
        self._subcontrollers: List[EventController] = []
        self._mutex = asyncio.Lock()  # Critical section lock

    @property
    def running(self) -> bool:
        "Returns bool indicating if the controller is running or not."
        return self._running

    @property
    def subcontrollers(self) -> List["EventController"]:
        "Returns a list of controller's sub-controllers."
        return self._subcontrollers[:]

    @property
    def listeners(self) -> List[EventListener]:
        "Returns a list of ~:class:`asyncio_event_hub.controller.EventListener`."
        return self._listeners[:]

    @asynccontextmanager
    async def critical(self):
        """
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
        Removes the sub-controller.
        The controller is automatically stopped.

        Parameters
        -----------
        controller: EventController
            The controller to remove.

        Raises
        ---------
        ValueError
            The ``controller`` parameter is not a subcontroller of the current controller

        Returns
        ---------
        asyncio.Future
            An awaitable Future object, which can be used to wait
            for the controller to stop.
        """
        self._subcontrollers.remove(controller)
        return controller.stop()

    def stop(self):
        """
        Stops event loop asynchronously

        Returns
        ----------
        asyncio.Future
            A Future object that can be used to await for the controller's task to stop
            and also the tasks of all the subcontrollers.
        """
        if self._running:
            self._running = False
            self._event_queue.put_nowait(("__dummy_event__", tuple(), {}, asyncio.Future()))

        return asyncio.gather(self._loop_task, *(c.stop() for c in self._subcontrollers))

    def add_listener(self, event: TEvent, fnc: Callable, predicate: Callable[[Any], bool] = None):
        """
        Registers the function ``fnc`` as an event listener for ``event``.
        
        Parameters
        ------------
        event: Union[Enum, str, int]
            The event of listener to add.
        fnc: Callable
            The function listener to add.
        predicate: Optional[Callable[[Any], bool]]
            Optional function parameter that accepts the same parameters as ``fnc`` and must return
            True, indicating the event ``fnc`` is to be called or not. If it returns False, the ``fnc`` does not
            get called after event is emitted.
        """
        listeners = self._listeners[event] = self._listeners.get(event, [])
        listeners.append(EventListener(fnc, predicate))

    def remove_listener(self, event: TEvent, fnc: Callable):
        """
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
        Decorator used to register the function as an event listener.

        Parameters
        ---------------
        event: Union[Enum, str, int]
            The event that needs to occur for the function to be called.
        """
        def _listen_decor(fnc: Callable):
            self.add_listener(event, fnc)
            return fnc

        return _listen_decor

    def emit(self, event: TEvent, *args, **kwargs) -> asyncio.Future:
        """
        .. versionadded:: 3.0

        Emits an ``event`` by calling all the registered listeners from the event loop.

        Parameters
        -----------
        event: Union[Enum, str, int]
            The event to emit.
        args
            Variadic positional arguments passed to event listeners.
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

        self._event_queue.put_nowait((event, args, kwargs, future))

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
        "Clears all emitted events from queue (recreates the queue)."
        self._event_queue = asyncio.Queue()

    async def event_loop(self):
        """
        Event loop task.
        """
        queue = self._event_queue
        listeners = self._listeners

        event_id: TEvent
        future: asyncio.Future

        while self._running:
            event_id, args, kwargs, future = await queue.get()

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
