=========================================
Registering event listeners (handlers)
=========================================

Before we can emit any events, we obviously need some way of responding to the events.
Asyncio Event Hub library allows functions to be registered as event responders, a.k.a event listeners.

Listeners can be either normal functions, async functions, bound methods or any other callable object.

They can be registered in 2 main ways:

1. Through :py:meth:`asyncio_event_hub.controller.EventController.add_listener` method.

   This is the primary way of adding event listeners and allows to register any callable object
   as a listener.
   
   It accepts 3 parameters, with ``event`` and ``fnc`` being mandatory, while
   ``predicate`` is optional.
   
   The ``event`` parameter refers to the actual event being emitted. This can be either
   a string, enum or an integer. When emitting the event, the same value must be used.
   
   The ``fnc`` is the actual callable object / function that we are registering as a listener.
   
   The ``predicate`` parameter is an optional function that must accepts the same parameters as ``fnc``
   and return a :class:`bool` value.
   It is basically a condition checker.
   The ``predicate`` function is always called before ``fnc`` and the ``fnc`` is only called if ``pridicate``
   function returns True after being called.

   .. code-block:: python
        :caption: Event listener without condition
        :emphasize-lines: 13

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


        asyncio.run(main())  # Start asyncio framework

    
   .. code-block:: python
        :caption: Event listener with a condition
        :emphasize-lines: 13

        import asyncio
        import asyncio_event_hub as aeh


        def event_listener(a: int = 1):
            print(f"Called listener, a={a}")


        async def main():
            ctrl = aeh.EventController()
            # Add a listener to "my_event", which gets called
            # when parameter 'a' receives value 5.
            ctrl.add_listener("my_event", event_listener, lambda a: a == 5)
            ctrl.start()  # Start the controller here.

            while True:
                await asyncio.sleep(5)


        asyncio.run(main())  # Start asyncio framework


2. Through :py:meth:`asyncio_event_hub.controller.EventController.listen` decorator.

   This method can be used to simplify the code required, however it can not be used
   for bound object methods. This is because the methods are just functions before an object is created,
   thus using a decorator would register a listener at class level.
   
   
   .. code-block:: python
       :caption: Event listener using a decorator
       :emphasize-lines: 6
   
       import asyncio
       import asyncio_event_hub as aeh
   
       ctrl = aeh.EventController()
   
       @ctrl.listen("my_event")  # Event listener (handler) registered with a decorator
       def event_listener(a: int = 1):
           print(f"Called listener, a={a}")
   
       async def main():
           ctrl.start()  # Start the controller here.
   
           while True:
               await asyncio.sleep(5)
   
   
           asyncio.run(main())  # Start asyncio framework
