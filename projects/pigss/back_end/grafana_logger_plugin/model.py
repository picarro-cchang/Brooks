from datetime import datetime
from traceback import format_exc

from common.sqlite_connection import SQLiteInstance


class EventsModel:
    @classmethod
    def build_sql_select_query(cls, query_params, table_name, log):
        """
        description: Given a query dictionary, create a sql statement
        params:
            query_params: dict
        returns:
            SQL Query: string
        """
        rowid = client = limit = level = start = limit_tpl = end = None

        try:
            if "columns" in query_params:
                columns = query_params["columns"]
            if "rowid" in query_params:
                rowid = query_params["rowid"]
            if "client" in query_params:
                client = query_params["client"]
            if "level" in query_params:
                level = [int(i) for i in query_params["level"]]
            if "start" in query_params:
                start = query_params["start"]
            if "end" in query_params:
                end = query_params["end"]
            if "limit" in query_params:
                limit = query_params["limit"]

            # Sequential Query Building, careful
            query = ""
            constraints = []
            values = []
            columns_tpl = (", ".join(columns))

            if rowid:
                constraints.append((f'rowid > ?'))
                values.append(rowid)
            if client:
                constraints.append(f'ClientName = ?')
                values.append(client)
            if level:
                # int values, so no issue of sql injection
                constraints.append(f'Level in ({", ".join([str(i) for i in level])})')
            if start and isinstance(start, int):
                constraints.append(f'EpochTime >= ?')
                values.append(start)
            if end and isinstance(end, int):
                constraints.append(f'EpochTime <= ?')
                values.append(end)
            if limit and isinstance(limit, int):
                limit_tpl = (f'LIMIT {limit}')

            # Respect the space between constraints
            query += f'SELECT {columns_tpl} FROM {table_name} '
            if len(constraints) > 0:
                query += f'WHERE {" AND ".join(constraints)} '
            query += f'ORDER BY rowid ASC '
            if limit_tpl:
                query += f'{limit_tpl}'
            query += ';'
        except ValueError as ve:
            log.error(f"Error in building query {ve} with query params {query_params}")
            log.debug(f"Error in building query {ve} with query params {query_params}", format_exc())
            return (None, None)
        except TypeError as te:
            log.error(f"Error in building query {te} with query params {query_params}")
            log.debug(f"Error in building query {te} with query params {query_params}", format_exc())
            return (None, None)
        return query, tuple(values)

    @classmethod
    def print_query(cls, query, values):
        """ Prints executed sql query, to be used for debug purpose

        Arguments:
            query {str} -- [description]
            values {[str]} -- [description]
        """
        new_query = ""
        j = k = 0
        for i, ch in enumerate(query):
            if ch == "?":
                new_query += str(f" {values[k]}")
                k += 1
            else:
                new_query += ch
        print(f"Query: {new_query}")

    @classmethod
    def execute_query(cls, sqlite_path, query, values, table_name, log):
        """
        Return rows of logs after applying query if query is not None, else
        returns all of the logs

        params:
            connection: Connection object
            query: tuple (level, limit, start, end?)
        return:
            dict of rows
        """
        if __debug__:
            cls.print_query(query, values)
        try:
            connection = SQLiteInstance(sqlite_path).get_instance()
            cursor = connection.cursor()
            result = cursor.execute(query, values)
            return result.fetchall()
        except FileNotFoundError:
            log.error("DB File does not exist.")
        except ConnectionError:
            log.error("Unable to connect to SQLite DB")

    @classmethod
    def close_connection(cls):
        SQLiteInstance.close_connection()
