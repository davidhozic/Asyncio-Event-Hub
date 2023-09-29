============
Guide
============

The events are being processed in something called :class:`~asyncio_event_hub.controller.EventController`.

The objects created from the class :class:`~asyncio_event_hub.controller.EventController` allow users
to emit custom events and assign event listeners to these emitted events. After an event is emitted, the controller
(in it's event loop task) calls all the listener functions in the same order they were assigned as listeners.


.. toctree::

    control
    register
