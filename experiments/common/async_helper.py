import asyncio
import functools
import time
import traceback
from threading import Thread


def log_async_exception(log_func=None, stop_loop=False, ignore_cancel=True):
    """
    A decorator that wraps the passed in coroutine and logs any uncaught exception and optionally stops the loop
    """
    if log_func is None:
        log_func = print

    def deco(coroutine):
        @functools.wraps(coroutine)
        async def wrapper(*args, **kwargs):
            try:
                await coroutine(*args, **kwargs)
            except Exception as e:
                if ignore_cancel and isinstance(e, asyncio.CancelledError):
                    pass
                else:
                    # log the exception and stop everything
                    log_func(f'\nCoroutine "{coroutine.__qualname__}" terminated due to exception\n' + " |"
                             "\n  | ".join(traceback.format_exc().splitlines()))
                    if stop_loop:
                        log_func("Stopping event loop due to unhandled exception in coroutine")
                        loop = asyncio.get_event_loop()
                        loop.stop()

        return wrapper

    return deco


class SyncWrapper:
    """Wraps an asyncio based class in a thread so that it can be interacted with 
    synchronously. A set of nominated coroutines of the class are exposed as blocking
    methods of the wrapper class.

    Suppose that we have a class `Simulator` which has an asynchronous method `cli`. We 
    execute

    sim = SyncWrapper(Simulator).wrap(['cli'])

    Parameters may be passed to the `__init__` method of `Simulator` as additional arguments
    to `SyncWrapper`. The argument of `wrap` is a list of methods in Simulator that we wish
    to call synchronously. Following this, we can use

    y = sim.cli(x)

    as a blocking (synchronous) call.

    See https://gist.github.com/dmfigol/3e7d5b84a16d076df02baa9f53271058
    """

    def __init__(self, cls, *a, **k):
        self.__class_to_wrap = cls
        self.__args = a
        self.__kwargs = k

    def __getattr__(self, name):
        if name in self.method_list:
            return lambda *a, **k: asyncio.run_coroutine_threadsafe(getattr(self.__sim, name)(*a, **k), self.__loop).result()
        else:
            raise AttributeError(f"No such attribute '{name}'")

    def __start_background_loop(self):
        async def setup():
            self.__sim = self.__class_to_wrap(*self.__args, **self.__kwargs)

        asyncio.set_event_loop(self.__loop)
        self.__loop.run_until_complete(setup())
        self.__loop.run_forever()

    def wrap(self, method_list):
        self.method_list = method_list
        self.__loop = asyncio.new_event_loop()
        t = Thread(target=self.__start_background_loop, daemon=True)
        t.start()
        time.sleep(0.01)
        return self


if __name__ == "__main__":

    @log_async_exception(stop_loop=True)
    async def my_task():
        i = 0
        while True:
            await asyncio.sleep(0.5)
            print('.', end='', flush=True)
            i += 1
            if i == 10:
                1 / 0

    async def main():
        asyncio.create_task(my_task())
        while True:
            await asyncio.sleep(1.0)
            print('+', end='', flush=True)

    loop = asyncio.get_event_loop()
    asyncio.ensure_future(main())
    loop.run_forever()
