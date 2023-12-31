from db_connection import DBInstance
import sqlite3


class EventsModel:

    @classmethod
    def build_sql_select_query(cls, query_params, table_name):
        """
        description: Given a query dictionary, create a sql statement
        params:
            query_params: dict
        returns:
            SQL Query: string
        """
        rowid = client = limit = level = start_date = limit_tpl = end_date = None
        columns = ["rowid", "ClientTimestamp",
                   "ClientName", "LogMessage", "Level"]

        try:
            if "columns" in query_params:
                columns = query_params["columns"]
            if "rowid" in query_params:
                rowid = query_params["rowid"]
            if "client" in query_params:
                client = query_params["client"]
            if "level" in query_params:
                level = query_params["level"]
            if "start_date" in query_params:
                start_date = query_params["start_date"]
            if "end_date" in query_params:
                end_date = query_params["end_date"]
            if "limit" in query_params:
                limit = query_params["limit"]

            # Sequential Query Building, careful
            query = ""
            constraints = []
            columns_tpl = (", ".join(columns))

            if rowid:
                constraints.append((f'rowid > {rowid}'))
            if client:
                constraints.append(f'ClientName = "{client}"')
            if level:
                constraints.append(f'Level in ({", ".join(level)})')
            if start_date:
                constraints.append(f'EpochTime >= {start_date}')
            if end_date:
                constraints.append(f'EpochTime <= {end_date}')
            if limit:
                limit_tpl = (f'LIMIT {limit}')

            # Respect the space between constraints
            query += f'SELECT {columns_tpl} FROM {table_name} '
            if len(constraints) > 0:
                query += f'WHERE {" AND ".join(constraints)} '
            query += f'ORDER BY rowid ASC '
            if limit_tpl:
                query += f'{limit_tpl}'
            query += ';'
        except Exception as ex:
            print("Exception", ex)
            return None
        return query

    @classmethod
    def build_select_default(cls, table_name):
        return (f"SELECT rowid, ClientTimestamp, ClientName, LogMessage, Level"
                f"FROM {table_name} ORDER BY rowid ASC LIMIT 20"
                )

    @classmethod
    def execute_query(cls, query, table_name):
        """
        Return rows of logs after applying query if query is not None, else 
        returns all of the logs

        params:
            connection: Connection object
            query: tuple (level, limit, start_date, end_date?)
        return:
            dict of rows
        """
        connection = DBInstance.get_instance()
        cursor = connection.cursor()
        result = cursor.execute(query)
        return result.fetchall()
