import time
import os
import sys
import asyncio
from six.moves import input
import datetime
import json
import threading
import traceback
import logging
import random
from abc import ABC, abstractmethod
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse, Message


import library.utils as utils
# from library.base_module_class import BaseModuleClass
from library.base_iothub_client import BaseIotHubClient, IobHubRemoteMethodStatus
from library.base_iothub_reader_client import BaseIotHubReaderClient
from library.measurement import Measurement, ModbusMeasurement, FunctionMeasurement



class BaseIotHubReaderModuleClient(BaseIotHubReaderClient):

    def __init__(self, machine_type, measurement_list, config_measurement_list=[], variables_dict=None):
        super().__init__(machine_type, measurement_list, config_measurement_list=config_measurement_list, variables_dict=variables_dict)


    async def _internal_send_message_(self, message, *args, **kwargs):
        if 'output' in kwargs:
            output = kwargs['output']
        elif len(args) > 0:
            output = args[0]
        else:
            output = 'output1'
        await self.iothub_client.send_message_to_output(message, output)
        

    async def _init_iothub_client_(self):
        self.iothub_client = IoTHubModuleClient.create_from_edge_environment()
    