
=========================
Sub-controllers
=========================

Asyncio Event Hub also supports inherited event emitting, meaning you can have multiple instances of
:class:`~asyncio_event_hub.controller.EventController` that can work on different levels.

A sub-controller is just a regular controller, that will automatically emit events if it's parent has emitted
them. Eg. we could have a global event controller that has global event handlers, and beside it
we could also have local controllers that have event handlers responsible for handling the same event at a more
narrow scope.


Adding a sub-controller
========================

To make a :class:`~asyncio_event_hub.controller.EventController` a sub-controller of some other
:class:`~asyncio_event_hub.controller.EventController`, we can use the
:py:meth:`asyncio_event_hub.controller.EventController.add_subcontroller` method.

The method will not make any changes to the original (now sub) controller. We can still
emit events to it and give it it's own event listeners. The method only forces is to receive the parent's events
from the :py:meth:`asyncio_event_hub.controller.EventController.emit` method. The sub-controller does not inherit
the parent's event listeners.


.. code-block:: python
    :caption: Adding a subcontroller
    :emphasize-lines: 21, 25, 26

    import asyncio
    import asyncio_event_hub as aeh


    def event_listener(a: int = 1):
        print(f"Called listener, a={a}")


    async def main():
        ctrl = aeh.EventController()  # Create master controller
        sub_ctrl = aeh.EventController()  # Create subcontroller

        # Add a listener to "my_event", which always gets called
        # regardless of value a receives (no condition).
        ctrl.add_listener("my_event", event_listener)
        sub_ctrl.add_listener("my_event", event_listener)

        ctrl.start()
        sub_ctrl.start()  # Optional, as it is automatically started when added as sub-controller

        ctrl.add_subcontroller(sub_ctrl)  # Add the sub-controller

        while True:
            await asyncio.sleep(5)
            await ctrl.emit("my_event", a=10)  # Emit the event to both ctrl and sub_ctrl
            await sub_ctrl.emit("my_event", a=20)  # Emit the event to only sub_ctrl


    asyncio.run(main())  # Start asyncio framework


Removing a sub-controller
=================================
A sub-controller can be removed from it's parent by calling the parent's
:py:meth:`asyncio_event_hub.controller.EventController.remove_subcontroller` method.

.. caution::

    The method does not automatically stop the sub-controller.
    If you wish to stop it, call :py:meth:`asyncio_event_hub.controller.EventController.stop` method manually!



.. code-block:: python
    :caption: Removing a subcontroller
    :emphasize-lines: 23

    import asyncio
    import asyncio_event_hub as aeh


    def event_listener(a: int = 1):
        print(f"Called listener, a={a}")


    async def main():
        ctrl = aeh.EventController()  # Create master controller
        sub_ctrl = aeh.EventController()  # Create subcontroller

        # Add a listener to "my_event", which always gets called
        # regardless of value a receives (no condition).
        ctrl.add_listener("my_event", event_listener)
        sub_ctrl.add_listener("my_event", event_listener)

        ctrl.start()
        sub_ctrl.start()  # Optional, as it is automatically started when added as sub-controller

        ctrl.add_subcontroller(sub_ctrl)  # Add the sub-controller
        await ctrl.emit("my_event", a=10)  # Emit the event to BOTH ctrl and sub_ctrl
        ctrl.remove_subcontroller(sub_ctrl)  # Remove the sub-controller

        while True:
            await asyncio.sleep(5)
            await ctrl.emit("my_event", a=10)  # Emit the event to ONLY ctrl


    asyncio.run(main())  # Start asyncio framework
