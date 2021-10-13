import time
import os
import sys
import asyncio
from six.moves import input
import datetime
import json
import library.utils as utils
import threading
import traceback
import logging
import random
from abc import ABC, abstractmethod
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse, Message



class BaseModuleClass(ABC):

    STATUS_OK = 200
    STATUS_NOT_FOUND = 404
    STATUS_ERROR = 500

    def __init__(self):
        self.alive_delay = 60
        self.alive_message = "I'M ALIVE"
        self.list_background_functions = []
        self.init_logging('log.main')
        

    def init_logging(self, filename, level=logging.DEBUG, stdout=True):
        # logging config
        # for key in logging.Logger.manager.loggerDict:
        #     print(key)
        # logging.basicConfig(filename=filename, filemode='w', level=logging.DEBUG, format='%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
        logging.basicConfig(filename=filename, filemode='w', format='%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        logging.getLogger("pymodbus").setLevel(logging.CRITICAL)
        logging.getLogger("azure.iot").setLevel(logging.CRITICAL)
        logging.getLogger("azure").setLevel(logging.CRITICAL)
        if stdout:
            logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        self.logger = logging.getLogger(__name__)


    def is_simulator(self):
        return utils.parse_bool(os.getenv("SIMULATOR", default=False), default=False)


    def is_enabled(self):
        return utils.parse_bool(os.getenv("ENABLED", default=True), default=True)


    def check_python_version(self):
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )


    async def send_message_json(self, module_client, results, output='output1'):
        json_message = json.dumps(results)
        message = Message(json_message)
        self.logger.info("SENDING MESSAGE to {}: {}".format(output, json_message))
        await module_client.send_message_to_output(message, output)

    
    def _init_module_client(self):
        self.module_client = IoTHubModuleClient.create_from_edge_environment()


    async def _connect_module_client(self):
        self.logger.info("CONNECTING TO MODULE CLIENT")
        await self.module_client.connect()
        self.logger.info("CONNECTED TO MODULE CLIENT")
    

    async def _disconnect_module_client(self):
        self.logger.info("DISCONNECTING  MODULE CLIENT")
        await self.module_client.disconnect()
        self.logger.info("DISCONNECTED FROM MODULE CLIENT")
    

    def stdin_listener(self):
        while True:
            self.logger.debug(self.alive_message)
            time.sleep(self.alive_delay)


    def _run_background(self, *functions):
        listeners = asyncio.gather(*[f(self.module_client) for f in functions])
        return listeners


    def _run_foreground(self):
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, self.stdin_listener)
        return user_finished


    async def _run_async(self):
        try:
            self.check_python_version()
            
            self._init_module_client()

            await self._connect_module_client()

            print('self.list_background_functions', self.list_background_functions)
            listeners = self._run_background(*self.list_background_functions)

            user_finished = self._run_foreground()

            await user_finished

            listeners.cancel()

            await self._disconnect_module_client()

        except Exception as e:
            print ( "Unexpected error %s " % e )
            raise


    def run(self):
        asyncio.run(self._run_async())
    