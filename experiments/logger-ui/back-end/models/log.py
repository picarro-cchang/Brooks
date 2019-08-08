from flask import g
from db_utils import get_connection


class EventsModel:

    def __init__(self, client_timestamp, client_name, epoch_time, log_message, level):
        self.client_timestamp = client_timestamp
        self.client_name = client_name
        self.epoch_time = epoch_time
        self.log_message = log_message
        self.level = level

    @classmethod
    def build_query(cls, query_params, table_name='Events'):
        """
        Build and return query for given paramneters

        params:
            query_params: dict
        return:
            query: string
        """
        print('-->', query_params)
        try:
            if 'columns' in query_params:
                columns = query_params['columns']
            else:
                columns = None
            if 'last_accessed_rowid' in query_params:
                last_accessed_rowid = query_params['last_accessed_rowid']
            else:
                last_accessed_rowid = None
            if 'client' in query_params:
                client = query_params['client']
            else:
                client = None
            if 'level' in query_params:
                level = query_params['level']
            else:
                level = None
            if 'start_date' in query_params:
                start_date = query_params['start_date']
            else:
                start_date = None
            if 'end_date' in query_params:
                end_date = query_params['end_date']
            else:
                end_date = None
            if 'limit' in query_params:
                limit = query_params['limit']
            else:
                limit = None

            # Sequential Query Building, careful
            query = ''
            constraints = []
            columns_tpl = (', '.join(columns)) if columns else '*'

            if last_accessed_rowid:
                constraints.append((f'rowid > {last_accessed_rowid}'))
            if client:
                constraints.append(f'ClientName = "{client}"')
            if level:
                constraints.append(f'Level = {level}')
            if start_date:
                constraints.append(f'EpochTime >= {start_date}')
            if end_date:
                constraints.append(f'EpochTime <= {end_date}')

            if limit:
                limit_tpl = (f'LIMIT {limit}')

            query += f'SELECT {columns_tpl} FROM {table_name} '
            query += f'WHERE {" AND ".join(constraints)} '
            query += f'ORDER BY rowid DESC {limit_tpl}'
            query += ';'
            print(query)
        except Exception as ex:
            print("Exception", ex)
            return f'SELECT * from {table_name}'
        return query

    @classmethod
    def execute_query(cls, query):
        """
        Return rows of logs after applying query if query is not None, else 
        returns all of the logs

        params:
            connection: Connection object
            query: tuple (level, limit, start_date, end_date?)
        return:
            dict of rows
        """
        connection = get_connection()
        cursor = connection.cursor()
        result = cursor.execute(query)
        return result.fetchall()
