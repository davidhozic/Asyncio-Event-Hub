=======================
Emitting events
=======================

After registering the events handlers, we can now emit corresponding events, which will cause
all the registered handlers to be called in the order they were registered and will happen so within the
:class:`~asyncio_event_hub.controller.EventController`'s event loop.

Events can be emitted by calling the :class:`asyncio_event_hub.controller.EventController.emit` method,
that accepts the ``event`` (string, enum or integer) and positional and keyword arguments that get passed to
all the event listeners (handlers).


.. code-block:: python
        :caption: Emitting event without waiting for it's processing to complete
        :emphasize-lines: 18

        import asyncio
        import asyncio_event_hub as aeh


        def event_listener(a: int = 1):
            print(f"Called listener, a={a}")


        async def main():
            ctrl = aeh.EventController()
            # Add a listener to "my_event", which always gets called
            # regardless of value a receives (no condition).
            ctrl.add_listener("my_event", event_listener)
            ctrl.start()  # Start the controller here.

            while True:
                await asyncio.sleep(5)
                ctrl.emit("my_event", a=10)  # Emit the event


        asyncio.run(main())  # Start asyncio framework


Optionally we can also ``await`` for the events to be fully processed.

.. code-block:: python
        :caption: Emitting event and waiting for it's processing to complete (``await``)
        :emphasize-lines: 18

        import asyncio
        import asyncio_event_hub as aeh


        def event_listener(a: int = 1):
            print(f"Called listener, a={a}")


        async def main():
            ctrl = aeh.EventController()
            # Add a listener to "my_event", which always gets called
            # regardless of value a receives (no condition).
            ctrl.add_listener("my_event", event_listener)
            ctrl.start()  # Start the controller here.

            while True:
                await asyncio.sleep(5)
                await ctrl.emit("my_event", a=10)  # Emit the event


        asyncio.run(main())  # Start asyncio framework


Event priority
====================
Asyncio Event Hub allows to prioritize events. Events with higher priority
always get emitted before the ones with lower priority.
The :class:`asyncio_event_hub.controller.EventController.emit` method accepts a keyword argument
``priority`` to control the priority level. It is an integer parameter,
where a higher integer means higher priority. The default priority is 0.


.. code-block:: python
    :caption: Emitting event and waiting for it's processing to complete (``await``)
    :emphasize-lines: 18

    import asyncio
    import asyncio_event_hub as aeh


    def event_listener(a: int = 1):
        print(f"Called listener, a={a}")


    async def main():
        ctrl = aeh.EventController()
        # Add a listener to "my_event", which always gets called
        # regardless of value a receives (no condition).
        ctrl.add_listener("my_event", event_listener)
        ctrl.start()  # Start the controller here.

        while True:
            await asyncio.sleep(5)
            # Emit the event with a=10
            ctrl.emit("my_event", a=10)
            # Emit the event with a=20. This will be executed before a=10 one.
            ctrl.emit("my_event", a=20, priority=1)

    asyncio.run(main())  # Start asyncio framework

