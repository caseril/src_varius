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
import logging.handlers
import random
from enum import Enum, auto
from abc import ABC, abstractmethod
# from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse, Message


class IobHubRemoteMethodStatus(Enum):
    STATUS_OK = 200
    STATUS_NOT_FOUND = 404
    STATUS_ERROR = 500



class BaseIotHubClient(ABC):

    # STATUS_OK = 200
    # STATUS_NOT_FOUND = 404
    # STATUS_ERROR = 500

    def __init__(self, machine_type, variables_dict=None):
        self.machine_type = machine_type
        self.variables_dict = utils.merge_dicts_priority(variables_dict, os.environ) #  os.environ if variables_dict is None else variables_dict
        self.alive_delay = 60
        self.alive_message = "I'M ALIVE"
        self.list_background_functions = []
        self.init_logging('log.main')
        self.iothub_client = None
        
    ######################################################################################################################

    def _get_(self, key, default=None):
        return utils.get(self.variables_dict, key, default=default)

    ######################################################################################################################

    def init_logging(self, filename, level=logging.DEBUG, stdout=True, maxBytes=10000, backupCount=5):
        # logging.basicConfig(filename=filename, filemode='w', format='%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
        logging.getLogger().setLevel(logging.NOTSET)
        logging.getLogger().handlers = []

        rotatingHandler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=maxBytes, backupCount=backupCount)
        rotatingHandler.setLevel(logging.DEBUG)
        rotatingHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(rotatingHandler)

        logging.getLogger(__name__).setLevel(level)
        logging.getLogger("pymodbus").setLevel(logging.CRITICAL)
        logging.getLogger("azure.iot").setLevel(logging.CRITICAL)
        logging.getLogger("azure").setLevel(logging.CRITICAL)
        if stdout:
            logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
        self.logger = logging.getLogger(__name__)
        self.logger.info('init_logging::end')

    ######################################################################################################################

    def is_simulator(self):
        return utils.parse_bool(self._get_("SIMULATOR"), default=False)


    def is_enabled(self):
        return utils.parse_bool(self._get_("ENABLED"), default=True)


    def is_config_enabled(self):
        return utils.parse_bool(self._get_("CONFIG_ENABLED"), default=True)


    def check_python_version(self):
        if not sys.version >= "3.5.3":
            raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )

    ######################################################################################################################

    async def send_message_json(self, module_client, message_json, *args, **kwargs): #output='output1'):
        message_str = json.dumps(message_json)
        message = Message(message_str)
        self.logger.info(f'send_message_json::{message_str}')
        await self._internal_send_message_(message, *args, **kwargs)


    async def call_remote_method(self, device_id, method_name, module_id=None, payload="{}", response_timeout=5, connect_timeout=5):
        method_params = {
            "methodName": method_name,
            "payload": payload,
            "responseTimeoutInSeconds": response_timeout,
            "connectTimeoutInSeconds": connect_timeout,
        }

        response = await self.iothub_client.invoke_method(method_params=method_params, device_id=device_id, module_id=module_id)
        return response

    ######################################################################################################################

    async def get_twin(self):
        # TODO TRY CATCH IN CASE OF ERRORS
        self.twin = await self.iothub_client.iothub_client.get_twin()['desired']
        return self.twin


    async def set_twin(self):
        # TODO TRY CATCH IN CASE OF ERRORS
        await self.iothub_client.patch_twin_reported_properties(self.twin) #twin['desired'])

    ######################################################################################################################
    ######################################################################################################################

    def stdin_listener(self):
        while True:
            if self.alive_message is not None:
                self.logger.debug(self.alive_message)
            time.sleep(self.alive_delay)


    def _run_background_(self, *functions):
        listeners = asyncio.gather(*[f(self.iothub_client) for f in functions])
        return listeners


    def _run_foreground_(self):
        loop = asyncio.get_event_loop()
        user_finished = loop.run_in_executor(None, self.stdin_listener)
        return user_finished


    async def _run_async_(self):
        try:
            self.check_python_version()
            
            await self._init_iothub_client_()

            await self._connect_module_client_()

            listeners = self._run_background_(*self.list_background_functions)

            user_finished = self._run_foreground_()

            await user_finished

            listeners.cancel()

            await self._disconnect_module_client_()

        except Exception as e:
            print ( "Unexpected error %s " % e )
            raise


    def run(self):
        asyncio.run(self._run_async_())
    

    ######################################################################################################################
    ######################################################################################################################

    @abstractmethod
    async def _internal_send_message_(self, message, *args, **kwargs):
        pass


    @abstractmethod
    async def _init_iothub_client_(self):
        pass


    async def _connect_module_client_(self):
        await self.iothub_client.connect()
    

    async def _disconnect_module_client_(self):
        await self.iothub_client.disconnect()
    
    ######################################################################################################################
    ######################################################################################################################

    def register_twin_properties_listener(self):
        self.list_background_functions.append(self.twin_properties_listener)


    async def twin_properties_listener(self, iothub_client):
        await utils.twin_properties_listener(iothub_client, self.twin_properties_updated, logger=self.logger)

    
    async def twin_properties_updated(self, patch):
        pass