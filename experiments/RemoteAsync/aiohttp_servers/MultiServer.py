import asyncio
import aiohttp
import attr
from aiohttp import web


async def handle1(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Hello, " + name
    return web.Response(text=text)


async def handle2(request):
    name = request.match_info.get('name', "Anonymous")
    text = "Goodbye, " + name
    return web.Response(text=text)

app1 = web.Application()
app1.add_routes([web.get('/', handle1),
                 web.get('/{name}', handle1)])

app2 = web.Application()
app2.add_routes([web.get('/', handle2),
                 web.get('/{name}', handle2)])


async def startup():
    runner1 = web.AppRunner(app1)
    await runner1.setup()
    site1 = web.TCPSite(runner1, 'localhost', 8081)
    await site1.start()
    print(f"======== Running on http://{site1._host}:{site1._port} ========")

    runner2 = web.AppRunner(app2)
    await runner2.setup()
    site2 = web.TCPSite(runner2, 'localhost', 8082)
    await site2.start()
    print(f"======== Running on http://{site2._host}:{site2._port} ========")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Stop server begin')
    finally:
        loop.close()
    print('Stop server end')
