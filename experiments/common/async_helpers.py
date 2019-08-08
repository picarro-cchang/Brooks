import asyncio
import functools
import traceback


def log_async_exception(coroutine):
    """
    A decorator that wraps the passed in co-routine and logs 
    an unhandled exception should one occur. Stops the current
    event loop if this happens.
    """

    @functools.wraps(coroutine)
    async def wrapper(*args, **kwargs):
        try:
            await coroutine(*args, **kwargs)
        except:
            # log the exception and stop everything
            print(traceback.format_exc())
            print("Stopping event loop due to unexpected exception in coroutine")
            # re-raise the exception
            asyncio.get_event_loop().stop()
            raise

    return wrapper
