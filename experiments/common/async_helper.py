import asyncio
import functools
import traceback


def log_async_exception(log_func=None, stop_loop=False):
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
            except Exception:
                # log the exception and stop everything
                log_func(f'\nCoroutine "{coroutine.__qualname__}" terminated due to exception\n', " |",
                         "\n  | ".join(traceback.format_exc().splitlines()))
                if stop_loop:
                    log_func("Stopping event loop due to unhandled exception in coroutine")
                    loop = asyncio.get_event_loop()
                    loop.stop()

        return wrapper

    return deco


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
