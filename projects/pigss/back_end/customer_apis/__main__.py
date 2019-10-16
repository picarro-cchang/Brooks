import asyncio
from traceback import format_exc

from main import main

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(asyncio.create_task(main())))
        loop.run_forever()
    except RuntimeError:
        print("Server Closed Unexpedly")
        print(format_exc())
    except KeyboardInterrupt:
        print("Server close initiated...")
    finally:
        print("Server Stopping...")
        loop.close()
