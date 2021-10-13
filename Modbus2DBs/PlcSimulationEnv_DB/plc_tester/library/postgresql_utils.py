from sqlalchemy import create_engine
import psycopg2 
import psycopg2.extras
import io
import os 
import logging
import traceback
import itertools
from io import StringIO
from library.base_db_manager import BaseDBManager
import library.utils as utils

# engine = create_engine('postgresql+psycopg2://username:password@host:port/database')

class Query():
    def __init__(self, query, params=None, fast=False):
        self.query = query
        self.params = params
        self.fast = fast


class PostgreSQLManager(BaseDBManager):

    def __init__(self, user=None, password=None, host=None, port=None, database=None, variables_dict=None, logger=None):
        super().__init__()
        variables_dict = utils.merge_dicts_priority(variables_dict, os.environ)

        self.user =      utils.get(variables_dict, "POSTGRESQL_USERNAME", default=None)    if user     is None else user 
        self.password =  utils.get(variables_dict, "POSTGRESQL_PASSWORD", default=None)    if password is None else password 
        self.host =      utils.get(variables_dict, "POSTGRESQL_HOST", default=None)        if host     is None else host 
        self.port =      utils.get(variables_dict, "POSTGRESQL_PORT", default=None)        if port     is None else port 
        self.database =  utils.get(variables_dict, "POSTGRESQL_DATABASE", default=None)    if database is None else database 
        self.logger   =  logger if logger is not None else logging.getLogger()


    @utils.overrides(BaseDBManager)
    def connect(self):
        # TODO IMPLEMENT RETRY POLICY
        # connection = psycopg2.connect(  user=os.getenv("POSTGRESQL_USERNAME"),
        #                                 password=os.getenv("POSTGRESQL_PASSWORD"),
        #                                 host=os.getenv("POSTGRESQL_HOST"),
        #                                 port=os.getenv("POSTGRESQL_PORT"),
        #                                 database=os.getenv("POSTGRESQL_DATABASE"))
        self.logger.info(f'Connecting to {self.user}@{self.host}:{self.port}/{self.database}.')
        self.connection = psycopg2.connect( user=self.user,
                                            password=self.password,
                                            host=self.host,
                                            port=self.port,
                                            database=self.database)

    
    @utils.overrides(BaseDBManager)
    def disconnect(self):
        if self.connection is not None:
            if not self.connection.closed:
                self.logger.info(f'Disconnecting from {self.user}@{self.host}:{self.port}/{self.database}.')
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
            # print ( connection.get_dsn_parameters(),"\n") # Print PostgreSQL Connection properties

            # executemany: 25s
            # execute_batch 12.5s
            # cursor.executemany(query, params)
            psycopg2.extras.execute_batch(cursor, query.query, query.params, page_size=500)

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
                import pandas
                results = pandas.DataFrame(results, columns=columns)

            return results
        except:
            print(traceback.format_exc())
        finally:
            # if(connection):
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