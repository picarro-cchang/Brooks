import asyncio
import os
import datetime
import json
from urllib.parse import parse_qs
from traceback import format_exc

from aiohttp import web

from back_end.servers.service_template import ServiceTemplate
from back_end.model.plan_model import PlanModel
from back_end.errors.plan_service_error import PlanExistsException, PlanRunningException, PlanDoesNotExistException

class PlanService(ServiceTemplate):
    def __init__(self, log, db_file):
        super().__init__()
        self.log = log
        self.db_file = db_file


    def setup_routes(self):
        self.app.router.add_post("/api/v0.1/plan", self.create)
        self.app.router.add_get("/api/v0.1/plan", self.read)
        self.app.router.add_put("/api/v0.1/plan", self.update)
        self.app.router.add_delete("/api/v0.1/plan", self.delete)

    async def on_startup(self, app):
        self.log.debug("PlanService is starting up")

        # Instantiate PlanModel
        self.model = PlanModel(self.log, self.db_file)


    async def on_shutdown(self, app):
        self.log.debug("PlanService is shutting down.")

    async def on_cleanup(self, app):
        # Do clean up stuff

        # Close Connection
        self.model.close_connection()

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
        plan_data = await request.json()
        name = plan_data.get('name')
        details = json.dumps(plan_data.get('details'))
        # TO DO: Get username from authentication token passed by front_end to avoid user imitation
        created_by = plan_data.get('user')
        # Current implementation has the creation of plan in local timezone
        created_at = str(datetime.datetime.now())
        try:
            rowid = self.model.create_plan(name, details, created_by, created_at)
            return web.json_response(data={
                "message": f"A plan named {name} has been created, and is available to be used in Setup.",
                "plan_id": rowid
            }, status=200)
        except PlanExistsException:
            # TO DO: Return names of all active plans present in the database for ease of use.
            return web.json_response(data={
                "message": f"A plan with name {name} already exists. Please try a different plan name."
            }, status=200)

        self.log.debug(f"Something unexpected has occurred {plan_data}")
        return web.json_response(data={
            "message": "Something unexpected has occurred."
        }, status=200)


    async def read(self, request):
        """
        description: Expose Read Plans

        tags:
            -   Plan Service Endpoints
        summary: This API can be used to read plans from the database, expects a JSON object
        produces:
            -   application/json
        response:
            "200":
                description: successful operation returns true
        """
        query_dict = parse_qs(str.lower(request.query_string))

        if "names" in query_dict and query_dict["names"][0] == "true":
            # Retrieve all plan names
            plan_names = self.model.read_plan_names()
            
            # If there is no active plan currently in the database.
            if not plan_names:
                return web.json_response(data={
                    "message": "There is no active plans in the database at this moment. Please create one."
                }, status=200)

            return web.json_response(data= {
                "plans": [name[0] for name in plan_names] # Each row is a list containing name
            }, status=200)

        elif "last_running" in query_dict and query_dict["last_running"][0] == "true":
            # Retrieve last running plan
            name, details = self.model.read_last_running_plan()

            if name is None and details is None:
                return web.json_response(data={
                    "message": "The system is not running any plan."
                }, status=200)

            return web.json_response(data={
                "name": name,
                "details": details
            }, status=200)

        elif "plan_name" in query_dict:
            # Given a plan name retrive the deatil of the plan
            plan_name = query_dict.get("plan_name")[0]
            try:
                name, details = self.model.read_plan_by_name(plan_name)
            except PlanDoesNotExistException:
                return web.json_response(data={
                    "message": f"No record could be found for plan name {plan_name}."
                }, status=200)

            return web.json_response(data={
                "name": name,
                "details": json.loads(details)
            }, status=200)

        self.log.debug(f"Something unexpected has occured. {query_dict}")
        return web.json_response(data= {
            "message": "Please make sure your using the API correctly."
        },status=200)

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
        plan_data = await request.json()
        name = plan_data.get("name")
        details = json.dumps(plan_data.get("details"))
        # TO DO: Get username from authentication token passed by front_end to avoid user imitation
        modified_by = plan_data.get('user')
        modified_at = str(datetime.datetime.now())
        is_deleted = plan_data.get("is_deleted", 0)
        updated_name = plan_data.get("updated_name", "")

        if plan_data.get("is_unloading") is not None:
            is_running = plan_data.get("is_running")
            is_unloading = plan_data.get("is_unloading")
            try:
                name, details = self.model.update_plan(name, details, modified_at, modified_by, is_running, is_deleted, updated_name, is_unloading)
                if name is not None and details is not None:
                    return web.json_response(data={
                        "message": f"Plan {name} has been updated with new details.",
                        "name": name,
                        "details": json.loads(details),
                        "is_running": is_running
                    })
            except PlanExistsException:
                return web.json_response(data = {
                    "message": f"The new plan name {updated_name} already exists. Please select a different new plan name."
                }, status=200)
            except PlanDoesNotExistException:
                return web.json_response(data={
                    "message": f"No record could be found for plan name {name}."
                }, status=200)
        else: 
            # Current implementation has the creation of plan in local timezone
            is_running = plan_data.get("is_running", 0)
            is_unloading = 0
            try:
                name, details = self.model.update_plan(name, details, modified_at, modified_by, is_running, is_deleted, updated_name,  is_unloading)
                if name is not None and details is not None:
                    return web.json_response(data={
                        "message": f"Plan {name} has been updated with new details.",
                        "name": name,
                        "details": json.loads(details),
                        "is_running": is_running
                    })
            except PlanRunningException:
                return web.json_response(data = {
                    "message": f"The plan {name} is currently running. It needs to be stopped before it can be updated."
                }, status=200)
            except PlanExistsException:
                return web.json_response(data = {
                    "message": f"The new plan name {updated_name} already exists. Please select a different new plan name."
                }, status=200)
            except PlanDoesNotExistException:
                return web.json_response(data={
                    "message": f"No record could be found for plan name {name}."
                }, status=200)

        self.log.debug(f"{plan_data} \n {format_exc()}")
        return web.json_response(data={
            "message": "Something unexpected has occurred. Please make sure entered data is valid."
        }, status=200)

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
        # plan_data = await request.json()
        query_dict = parse_qs(request.query_string)
        # name = plan_data.get("name")
        name = query_dict.get("name")[0] if query_dict.get("name") is not None else None 
        # TO DO: Get username from authentication token passed by front_end to avoid user imitation
        # modified_by = plan_data.get('user')
        modified_by = query_dict.get("user")[0] if query_dict.get("user") is not None else None
        # Current implementation has the creation of plan in local timezone
        modified_at = str(datetime.datetime.now())
        is_deleted = 1

        if not name:
            return web.json_response(data={
                "message": "Please make sure to provide a valid plan name."
            }, status=200)

        try:
            status = self.model.delete_plan(name, modified_at, modified_by, is_deleted)
            if status:
                return web.json_response(data={
                    "message": f"The plan {name} has been successfully deleted."
                }, status=200)
        except PlanRunningException:
            return web.json_response(data = {
                "message": f"The plan {name} is currently running. It needs to be stopped before it can be deleted."
            }, status=200)
        except PlanDoesNotExistException:
            return web.json_response(data={
                "message": f"No record could be found for plan name {name}."
            }, status=200)
        
        self.log.debug(f"{name} \n {format_exc()}")
        return web.json_response(data={
            "message": "Something unexpected has occurred. Please make sure you're deleting a valid plan."
        }, status=200)


if __name__ == "__main__":
    """
    In order for this service to run standalone, lologger needs to be running.
    """
    from aiohttp import web
    from aiohttp_swagger import setup_swagger
    import aiohttp_cors

    from back_end.lologger.lologger_client import LOLoggerClient

    log = LOLoggerClient(client_name="PlanService", verbose=True)
    # Get DB file path from config, and pass in instance as db_file
    db_file = os.path.join(os.getenv("HOME"), ".config", "pigss", "data", "sam_data.db")
    service = PlanService(log, db_file)

    cors = aiohttp_cors.setup(
        service.app, defaults={"*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )})

    for route in service.app.router.routes():
        print("route ->", route)
        cors.add(route)

    web.run_app(service.app, host="0.0.0.0", port=8080)
