from aiohttp import web, WSMsgType


class LoggerServer:
    """
    """

    def __init__(self):
        app = web.Application()
        app.add_routes([web.get("/ws", websocket_handler)])

    async def websocket_handler(request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == "close":
                    await ws.close()
                else:
                    print(f"msg data {msg.data}")
                    await ws.send_str("response")
            elif msg.type == WSMsgType.ERROR:
                ws.exception()

        print("websocket connection closed")
        return ws

