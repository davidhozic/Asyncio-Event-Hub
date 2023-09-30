=============
Control
=============

Starting the event controller
===============================

The event controller (event loop) can be started with the :py:meth:`asyncio_event_hub.controller.EventController.start` method,
which spins up an asyncio task inside and sleeps until en event is emitted. Since it creates a task, the asyncio
framework must already be running.

.. code-block:: python
    :emphasize-lines: 6, 7

    import asyncio
    import asyncio_event_hub as aeh


    async def main():
        ctrl = aeh.EventController()
        ctrl.start()  # Start the controller here.

        while True:
            await asyncio.sleep(5)

    

    asyncio.run(main())  # Start asyncio framework (asyncio's own event loop)



Stopping the event controller
===============================
Similar to how it can be started, the controller can be stopped with a method, in this case the method being
:py:meth:`asyncio_event_hub.controller.EventController.stop`.

This method will instruct the controller to finish processing all the events and then stop it's event loop,
but it will do so asynchronously. This means that after calling the function and returning from it, the event controller
is still running. If there is a requirement of waiting for the controller to stop, the method can also be awaited
with the ``await`` keyword (the method returns an awaitable :class:`asyncio.Future` object).


.. code-block:: python
    :emphasize-lines: 13
    :caption: Not waiting for the controller to stop

    import asyncio
    import asyncio_event_hub as aeh


    async def main():
        ctrl = aeh.EventController()
        ctrl.start()  # Start the controller here.

        while True:
            await asyncio.sleep(5)
            break

        ctrl.stop()  # Instruct the controller to stop asynchronously (not stopped instantly)
        await asyncio.sleep(5)


    asyncio.run(main())  # Start asyncio framework (asyncio's own event loop)


.. code-block:: python
    :emphasize-lines: 13
    :caption: Waiting for the controller to stop

    import asyncio
    import asyncio_event_hub as aeh


    async def main():
        ctrl = aeh.EventController()
        ctrl.start()  # Start the controller here.

        while True:
            await asyncio.sleep(5)
            break

        await ctrl.stop()  # Instruct the controller and await until it is stopped


    asyncio.run(main())  # Start asyncio framework (asyncio's own event loop)
