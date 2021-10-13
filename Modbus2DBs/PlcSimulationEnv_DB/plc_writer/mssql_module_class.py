import pyodbc
import pandas as pd
import io
import os 
import logging
import traceback
import itertools
from io import StringIO
from library.base_db_manager import BaseDBManager
import library.utils as utils

class Query():
    def __init__(self, query, params=None, fast=False):
        self.query = query
        self.params = params
        self.fast = fast


class MSSQLManager(BaseDBManager):

    def __init__(self, user=None, password=None, server=None, database=None, config_dict=None, logger=None):
        super().__init__()
        self.config_dict = utils.merge_dicts_priority(config_dict, os.environ)

        self.user =      utils.get(self.config_dict, "USERNAME", default=None)    if user     is None else user 
        self.password =  utils.get(self.config_dict, "PASSWORD", default=None)    if password is None else password 
        self.server =      utils.get(self.config_dict, "SERVER", default=None)    if server     is None else server 
        self.database =  utils.get(self.config_dict, "DATABASE", default=None)    if database is None else database 
        self.logger   =  logger if logger is not None else logging.getLogger()

    def init_testing(self, data_source =None, machine_twin=None, sensor_data=None):
        self.data_source =      utils.get(self.config_dict, "DATA_SOURCE", default=None)    if data_source     is None else data_source
        self.machine_twin =  utils.get(self.config_dict, "MACHINE_TWIN", default=None)    if machine_twin is None else machine_twin 
        self.sensor_data =      utils.get(self.config_dict, "SENSORS_DATA", default=None)    if sensor_data     is None else sensor_data 

    @utils.overrides(BaseDBManager)
    def connect(self):
        # TODO IMPLEMENT RETRY POLICY
        # connection = psycopg2.connect(  user=os.getenv("POSTGRESQL_USERNAME"),
        #                                 password=os.getenv("POSTGRESQL_PASSWORD"),
        #                                 host=os.getenv("POSTGRESQL_HOST"),
        #                                 port=os.getenv("POSTGRESQL_PORT"),
        #                                 database=os.getenv("POSTGRESQL_DATABASE"))
        self.logger.info(f'Connecting to {self.user}@{self.server}/{self.database}.')
        self.connection = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server+';DATABASE='+self.database+';UID='+self.user+';PWD='+ self.password)

    
    @utils.overrides(BaseDBManager)
    def disconnect(self):
        if self.connection is not None:
            if not self.connection.closed:
                self.logger.info(f'Disconnecting from {self.user}@{self.server}/{self.database}.')
                self.connection.close()

    
    # def get_connection(self):
    #     if self.connection is None:
    #         self.connect()

    #     return self.connection


    @utils.overrides(BaseDBManager)
    def query_execute_many(self, query: Query, commit=False, fetch=False, aslist=False, asdataframe=False, columns=None):

        # connection  = None
        cursor      = None
        try:
            connection = self.get_connection()

            cursor = connection.cursor()

            # executemany: 25s
            # execute_batch 12.5s
            # cursor.executemany(query, params)
            cursor.executemany(query.query, query.params)

            if commit:
                connection.commit()

        except:
            print(traceback.format_exc())
        finally:
            # if(connection):
            cursor.close()
                # connection.close()


    @utils.overrides(BaseDBManager)
    def query_execute(self, query: Query, commit=False, fetch=False, aslist=False, asdataframe=False, columns=None):
        cursor      = None
        try:
            connection = self.get_connection()

            cursor = connection.cursor()
            # print ( connection.get_dsn_parameters(),"\n") # Print PostgreSQL Connection properties

            cursor.execute(query.query)

            results = None

            if fetch:
                results = []
                row = cursor.fetchone()
                while row:
                    results_list = list()
                    for el in list(row):
                        if isinstance(el, str):
                            results_list.append(el.strip())
                        elif isinstance(el, float):
                            results_list.append(round(el, 7))  # TODO
                        else:
                            results_list.append(el)
                    results.append(results_list)
                    row = cursor.fetchone()
                    
            if commit:
                connection.commit()

            if results is not None and aslist:
                results = list(itertools.chain(*results))
            elif results is not None and asdataframe:
                results = pd.DataFrame(results, columns=columns)

            return results
        except:
            print(traceback.format_exc())
        finally:
            if(connection):
                cursor.close()
            #    connection.close()


    @utils.overrides(BaseDBManager)
    def query_execute_list(self, query_list, commit=False):
        cursor      = None
        try:
            connection = self.get_connection()

            cursor = connection.cursor()
            # print ( connection.get_dsn_parameters(),"\n") # Print PostgreSQL Connection properties

            for query in query_list:
                # cursor.fast_executemany = query.fast # TODO find an alternative
                
                if query.params is None:
                    cursor.execute(query.query)
                else:
                    if len(query.params) > 0:
                        cursor.executemany(query.query, query.params)          
                    
            if commit:
                connection.commit()


        except:
            if cursor is not None:
                cursor.rollback()

            print(traceback.format_exc())
        finally:
            # if(connection):
            cursor.close()
            #    connection.close()


    @utils.overrides(BaseDBManager)
    def query_execute_copy(self, df, destination_table, columns=None, commit=False):
        cursor      = None
        try:
            connection = self.get_connection()

            cursor = connection.cursor()
            
            f = StringIO()
            df.to_csv(f, sep=',', header=False, index=False, quoting=3)
            f.seek(0)

            cursor.copy_from(f, destination_table, columns=columns, sep=',')

            if commit:
                connection.commit()

        except:
            # if cursor is not None:
            #     cursor.rollback()
            if connection is not None:
                print('ROLLBACK')
                connection.rollback()

            print(traceback.format_exc())
        finally:
            # if(connection):
            cursor.close()
            #    connection.close()



# TESTING

if __name__=='__main__':
    server = 'greta-simulation.database.windows.net'
    database = 'regasphere_dev'
    user = 'rose_reader@greta-simulation'
    password = 'suguc88hHjk57wsGPVeM'
    mssql_client = MSSQLManager(user, password, server, database)
    query_str = "select time, value \
            from vw_sensors_data \
            where time > '2021/02/27 08:00:00'\
                and machine_name  = 'sandonato_ingrid_certosa' \
                    and sensor_type = 'MASSFLOW'  \
            order by time asc"
    query = Query(query_str)
    res = mssql_client.query_execute(query, commit=False, fetch=True, asdataframe=True, columns=['time', 'value'])
    print(res)