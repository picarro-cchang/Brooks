import os
import sqlite3
from traceback import format_exc

from back_end.errors.plan_service_error import PlanExistsException, PlanRunningException, PlanDoesNotExistException

class PlanModel:

    def __init__(self, log, db_file):
        self.db_connection = self.create_connection(db_file)
        self.log = log

        if self.db_connection:
            # Create Plans Table
            create_plan_table_query = '''CREATE TABLE IF NOT EXISTS plans (
                id integer PRIMARY KEY AUTOINCREMENT,
                name text NOT NULL,
                details JSON NOT NULL,
                created_by text NOT NULL,
                created_at text NOT NULL,
                is_running integer NOt NULL DEFAULT 0,
                is_deleted integer NOT NULL DEFAULT 0,
                modified_at text DEFAULT null,
                modified_by text DEFAULT null
            )
            '''
            self.create_plan_table(create_plan_table_query)

    def create_connection(self, db_file):
        connection = None
        try:
            connection = sqlite3.connect(db_file)
        except ConnectionError:
            self.error("Unable to connect to SQLite Database.")
        except Exception:
            self.log.debug(format_exc())
        return connection

    def close_connection(self):
        """ Close SQLite db connection
        """
        self.db_connection.close()

    def create_plan_table(self, create_plan_table_query):
        """ Create table in the db file, if doesn't exist already.
        """
        try:
            cur = self.db_connection.cursor()
            cur.execute(create_plan_table_query)
            self.db_connection.commit()
        except Exception:
            self.log.critical("Unable to create Plan table in database.")
            self.log.debug(format_exc())

    def is_valid_plan_name(self,  name):
        check_plan_name_exists = ''' SELECT * FROM plans where name = ? and is_deleted = 0 ORDER BY id DESC LIMIT 1'''
        try:
            cur = self.db_connection.cursor()
            # Check if a plan with same name already exists
            records = cur.execute(check_plan_name_exists, (name, ))
            rows = records.fetchone()
            if not rows:
                return True
        except sqlite3.OperationalError:
            self.log.debug(format_exc())
        return False

    def is_plan_running(self,  name):
        check_plan_name_exists = ''' SELECT * FROM plans where name = ? and is_running = 1 ORDER BY id DESC LIMIT 1'''
        try:
            cur = self.db_connection.cursor()
            # Check if a plan with same name already exists
            records = cur.execute(check_plan_name_exists, (name, ))
            rows = records.fetchone()
            if rows:
                return True
        except sqlite3.OperationalError:
            self.log.debug(format_exc())
        return False

    def create_plan(self, name, details, created_by, created_at, modified_at=None, modified_by=None):
        """ Create Plan in database
        
        Args:
            name: Name of the plan, must be unique
            details: Steps in the plan in JSON format
            created_by: The username of creator of the plan
            created_at: The date at which plan was created
            modified_at: The date at which plan was modified
            modified_by: The user who modified the plan
        
        Returns:
            True
            False

        Raises:
            PlanAlreadyExists: If a file with same name already exists.
        """
        insert_query = ''' INSERT INTO plans (name, details, created_by, created_at) VALUES (?, ?, ?, ?)'''
        
        plan = (name, details, created_by, created_at)
        try:
            cur = self.db_connection.cursor()
            if not self.is_valid_plan_name(name):
                raise PlanExistsException()
            else:
                cur.execute(insert_query, plan)
            self.db_connection.commit()
            return cur.lastrowid
        except sqlite3.DataError:
            self.log.critical("Unable to create the specified Plan in database.")
            self.log.debug(format_exc())
        except sqlite3.OperationalError:
            self.log.debug(format_exc())

    def read_plan_by_name(self, name):

        """ Given a name, returns the details for the plan

        Args:
            name: str

        Returns:
            Tuple (name, details)

        Raises:
            PlanNotFoundException: If a plan specified by name does not exist or is deleted
        """
        try:
            read_query = '''SELECT name, details FROM plans WHERE name = ? AND is_deleted != 1'''
            cur = self.db_connection.cursor()
            record = cur.execute(read_query, (name, )).fetchone()
            if record:
                return record
            raise PlanDoesNotExistException()
        except sqlite3.OperationalError:
            self.log.debug(f"name: {name} {format_exc()}")
        return None, None

    def read_plan_names(self):
        """ Return all available non-deleted plan names from the database.

        Args:
            None

        Returns:
            Array of plan names
        
        Raises:
            None
        """
        try:
            read_query = ''' SELECT name FROM plans WHERE is_deleted != 1'''
            cur = self.db_connection.cursor()
            records = cur.execute(read_query).fetchall()
            return records
        except sqlite3.OperationalError:
            self.log.debug(format_exc())

    def read_last_running_plan(self):
        """ Return last running plan by the service.

        Args:
            None

        Returns:
            Tuple (name, details)

        """
        try:
            read_query = '''SELECT name, details FROM plans WHERE is_running = 1'''
            record = self.db_connection.cursor().execute(read_query).fetchone()
            if record:
                return record
        except sqlite3.OperationalError:
            self.log.debug(format_exc())
        return None, None

    def update_plan(self, name, details, modified_at=None, modified_by=None, is_running=0, is_deleted=0, updated_name=""):
        """ Given a plan name and required data, update a plan

        Args:            
            name: Name of the plan, must be unique
            details: Steps in the plan in JSON format
            is_deleted: If the plan is active
            is_running: If the plan is currently running
            started_by: The username of the user startring the plan
            modified_at: The date at which plan was modified
            modified_by: The user who modified the plan

        Returns:
            rowid: Returns name and details of the successfully updated plan.
        """
        update_query = ''' UPDATE plans
                            SET details = ?,
                            modified_at = ?,
                            modified_by = ?,
                            is_running = ?,
                            is_deleted = ?
                            where name = ?
                             '''
        if self.is_plan_running(name):
            raise PlanRunningException()
        
        # if updated_name and not self.is_valid_plan_name(updated_name):
        #     raise PlanExistsException()

        values = (details, modified_at, modified_by, is_running, is_deleted, name)
        
        if updated_name:
            update_query = ''' UPDATE plans
                    SET name = ?,
                    details = ?,
                    modified_at = ?,
                    modified_by = ?,
                    is_running = ?,
                    is_deleted = ?
                    where name = ?
                '''
            values = (updated_name, details, modified_at, modified_by, is_running, is_deleted, name)

        try:
            cur = self.db_connection.cursor()
            recods = cur.execute(update_query, values)
            self.db_connection.commit()
            return (name, details) if not updated_name else (updated_name, details)
        except sqlite3.OperationalError:
            self.log.debug(format_exc())
        return None, None

    def delete_plan(self, name, modified_at, modified_by, is_deleted=1):
        """ Given a plan name, delete the plan from database i.e. set is_deleted=1

        Args:
            name: Name of the plan that needs to be deleted

        Returns:
            status: True if successfully deleted else False
        """
        if self.is_plan_running(name):
            raise PlanRunningException()

        # If a plan with name does not exist, it cannot be deleted
        if self.is_valid_plan_name(name):
            raise PlanDoesNotExistException()
    
        values = (is_deleted, modified_at, modified_by, name)
        delete_query = ''' UPDATE plans
                            SET is_deleted = ?,
                            modified_at = ?,
                            modified_by = ?
                            WHERE name = ?
                        '''
        try:    
            cur = self.db_connection.cursor()
            records = cur.execute(delete_query, values)
            self.db_connection.commit()
            return True
        except sqlite3.OperationalError:
            self.log.debug(format_exc())
        return False
