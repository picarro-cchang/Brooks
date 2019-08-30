from aiohttp import web


class BankNameService:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route("GET", "/", self.health_check)
        self.app.router.add_route("GET", "/search", self.search)
        self.app.router.add_route("POST", "/search", self.search)
        self.app.on_startup.append(self.on_startup)
        self.app.on_shutdown.append(self.on_shutdown)

    async def on_startup(self, app):
        pass

    async def on_shutdown(self, app):
        print("BankName server is shutting down")

    async def health_check(self, request):
        """
        description: Used to check theat data source exists and works

        tags:
            -   bank name service
        summary: Used to check theat data source exists and works
        produces:
            -   application/text
        responses:
            "200":
                description: successful operation.
        """
        return web.Response(text='This datasource is healthy.')

    async def search(self, request):
        """
        description: Gets the names of the valves available

        tags:
            -   bank name service
        summary:  Gets the names of the valves available
        produces:
            -   application/json
        responses:
            "200":
                description: successful operation.
        """
        controller = request.app['farm'].controller
        bank_names = controller.get_bank_names()

        ports = []
        valve_pos = 1
        for bank in [1, 2, 3, 4]:
            bank_dict = bank_names[str(bank)]
            for channel in [1, 2, 3, 4, 5, 6, 7, 8]:
                chan_dict = bank_dict["channels"]
                descr = f"{bank_dict['name']} {chan_dict[str(channel)]}"
                ports.append(dict(text=f"{valve_pos}: {descr}", value=str(valve_pos)))
                valve_pos += 1
        return web.json_response(ports)
