============================================
Async-Event-Loop
============================================

Async-Event-Loop is a library that provides users with a way to easily create
event-driven applications within the asyncio framework. It provides one main class
``async_event_loop.EventController``, which can be used to emit and add listeners (functions) to events
that get called from the event loop in the same order they were added.


Installation
==============
.. code-block:: bash

    pip install async-event-loop


Example
=============
.. code-block:: python

    import async_event_loop as ael
    import asyncio


    # Create event controllers
    main_controller = ael.EventController()
    sub_controller = ael.EventController()

    # Register sub_controller as a sub-controller of the main_controller
    main_controller.add_subcontroller(sub_controller)


    # Add listener via a decorator
    @main_controller.listen("my_event")
    async def listener1(a, b):
        print(f"listener1({a}, {b})")


    # Add listeners via a decorator
    @main_controller.listen("my_event")
    @sub_controller.listen("my_event")
    def listener2(a, b):
        print(f"listener2({a}, {b})")


    async def stop(a):
        main_controller.stop()  # Stop main_controller and it's sub-controllers.


    # Add listener through function
    main_controller.add_listener("stop_event", stop, predicate=lambda a: a == 5)  # Only call stop(a) if a is equal to 5


    async def main():
        main_controller.start()  # Start main_controller and it's sub-controllers.

        # Emit events into the event loop, executed asynchronously.
        # listener1 is called once, listener2 is caller twice -
        # once from main controller's event loop and once sub-controller's event loop. (not at this line, but asynchronously)
        main_controller.emit("my_event", a=9, b =10)

        # listener2 is called once from sub-controller's event loop. (not at this line, but asynchronously)
        sub_controller.emit("my_event", a=1, b=2)

        # await used to await for all listeners to finish processing event.
        await main_controller.emit("stop_event", a=1)  # Does not actually call anything since we have a predicate of a == 5.
        await main_controller.emit("stop_event", a=5)  # Stops controller asynchronously

    asyncio.run(main())
