import io
import os 
import logging
import traceback
import itertools
from io import StringIO
from abc import ABC, abstractmethod
from typing import List

# engine = create_engine('postgresql+psycopg2://username:password@host:port/database')

class Query():
    def __init__(self, query, params=None, fast=False):
        self.query = query
        self.params = params
        self.fast = fast


class BaseDBManager(ABC):

    def __init__(self):
        self.connection = None

    
    @abstractmethod
    def connect(self):
        pass

    
    @abstractmethod
    def disconnect(self):
        pass

    
    def get_connection(self):
        if self.connection is None:
            self.connect()

        return self.connection


    @abstractmethod
    def query_execute_many(self, query: Query, params, commit=False, fetch=False, aslist=False, asdataframe=False, columns=None):
        pass


    @abstractmethod
    def query_execute(self, query: Query, commit=False, fetch=False, aslist=False, asdataframe=False, columns=None):
        pass


    @abstractmethod
    def query_execute_list(self, query_list: List[Query], commit=False):
        pass


    @abstractmethod
    def query_execute_copy(self, df, destination_table, columns=None, commit=False):
        pass