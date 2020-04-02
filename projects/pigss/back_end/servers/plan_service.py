import asyncio

from aiohttp import web

from back_end.servers.service_template import ServiceTemplate
from back_end.model.plan_model import PlanModel

class PlanService(ServiceTemplate):
    def __init__(self, log, farm=None):
        super().__init__()
        self.log = log
        self.farm = farm


    def setup_routes(self):
        self.app.router.add_post("/plan/v0.1/create", self.create)
        self.app.router.add_get("/plan/v0.1/read", self.read)
        self.app.router.add_put("/plan/v0.1/update", self.update)
        self.app.router.add_delete("/plan/v0.1/delete", self.delete)

    async def on_startup(self, app):
        self.log.debug("PlanService is starting up")
        
        # Get DB file path from config, and pass in instance as db_file

        # Instantiate PlanModel
        self.model = PlanModel(self.log)
        

    async def on_shutdown(self, app):
        self.log.debug("PlanService is shutting down.")

    async def on_cleanup(self, app):
        # Do close up stuff

        # Close Connection
        pass

    async def create(self, request):
        """
        description: Create Plans

        tags:
            -   Plan Service Endpoints
        summary: This API can be used to create plans in the database, expects a JSON object
        produces:
            -   application/json
        response:
            "200":
                description: successful operation returns true
        """
        pass

    async def read(self, request):
        """
        description: Create Plans

        tags:
            -   Plan Service Endpoints
        summary: This API can be used to create plans in the database, expects a JSON object
        produces:
            -   application/json
        response:
            "200":
                description: successful operation returns true
        """
        return web.json_response(self.model.read_plan())

    async def update(self, request):
        """
        description: Create Plans

        tags:
            -   Plan Service Endpoints
        summary: This API can be used to create plans in the database, expects a JSON object
        produces:
            -   application/json
        response:
            "200":
                description: successful operation returns true
        """
        pass

    async def delete(self, request):
        """
        description: Create Plans

        tags:
            -   Plan Service Endpoints
        summary: This API can be used to create plans in the database, expects a JSON object
        produces:
            -   application/json
        response:
            "200":
                description: successful operation returns true
        """
        pass


if __name__ == "__main__":
    from aiohttp import web
    from aiohttp_swagger import setup_swagger
    import aiohttp_cors

    from back_end.lologger.lologger_client import LOLoggerClient

    log = LOLoggerClient(client_name="PlanService", verbose=True)
    service = PlanService(log)

    cors = aiohttp_cors.setup(
        service.app, defaults={"*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )})

    for route in service.app.router.routes():
        cors.add(route)

    web.run_app(service.app, host="0.0.0.0", port=8080)
