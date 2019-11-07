import sys
import asyncio

from main import main

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(asyncio.create_task(main(sys.argv[1:]))))
        loop.run_forever()
    except RuntimeError:
        print("Server closed unexpectedly")
        from traceback import format_exc

        print(format_exc())
    finally:
        print("Server Stopping...\n")
        loop.close()
