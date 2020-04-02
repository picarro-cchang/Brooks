import os
import sqlite3
from traceback import format_exc

class PlanModel:

    def __init__(self, log, db_file=None):
        db_file = os.path.join(os.getenv("HOME"), ".config", "pigss", "data", "sam_data.db")
        self.db_connection = self.create_connection(db_file)
        self.log = log

        if self.db_connection:
            # Create Plans Table
            create_plan_table_query = """ CREATE TABLE IF NOT EXISTS plans (
                id integer AUTOINCREMENT PRIMARY KEY,
                name text NOT NULL UNIQUE,
                plan_details JSON NOT NULL,
                created_by text NOT NULL,
                created_at text NOT NULL,
                modified_at text,
                modified_by text,
                is_active integer NOT NULL
            )
            """
            self.create_table(create_plan_table_query)

    def create_connection(self, db_file):
        connection = None
        try:
            connection = sqlite3.connect(db_file)
        except ConnectionError:
            self.error("Unable to connect to SQLite Database.")
        except Exception:
            self.log.debug(format_exc())
        return connection

    def create_table(self, query):
        """ Create table in the db file, if doesn't exist already.
        """
        try:
            cur = self.db_connection.cursor()
            cur.execute(query)
        except Exception:
            self.log.critical("Unable to create Plan table in database.")
            self.log.debug(format_exc())

    def create_plan(self, name, plan_details, created_by, created_at, modified_at=None, modified_by=None, is_active=0):
        """ Create Plan in database
        
        Args:
            name: Name of the plan, must be unique
            plan_details: Steps in the plan in JSON format
            created_by: The username of creator of the plan
            created_at: The date at which plan was created
            modified_at: The date at which plan was modified
            modified_by: The user who modified the plan
            is_active: If the plan is active
        
        Returns:
            True
            False

        Raises:
            FileAlreadyExists: If a file with same name already exists.
        """

    def read_plan(self):

        return {
            "message": "OK from read_plan"
        }

    def update_plan(self):
        pass

    def delete_plan(self):
        pass

    def close_connection(self):
        pass
