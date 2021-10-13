
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


# from library.base_module_class import BaseModuleClass
# from library.base_reader_module_class import BaseReaderModuleClass
from library.base_iothub_reader_module_client import BaseIotHubReaderModuleClient
from library.base_iothub_client import IobHubRemoteMethodStatus
from library.rtu_modbus import RtuModbus
from library.measurement import Measurement, ModbusMeasurement
import library.utils as utils


class RtuModuleClass(BaseIotHubReaderModuleClient):

    MACHINE_TYPE = "MICROTURBINE"

    def __init__(self):
        super().__init__(self.MACHINE_TYPE, None, None)
        measurement_list = utils.get_all_measurement_list(self.MACHINE_TYPE, os.environ)
        config_measurement_list = utils.get_config_measurement_list(RtuModuleClass.MACHINE_TYPE, os.environ, logger=self.logger)

        self.measurement_list = measurement_list
        self.config_measurement_list = config_measurement_list
        # self.list_background_functions.append(self.set_interval_listener_directmethod)
        self.simulator_setpoint = None

#############################################################################################
    async def init_device_instance(self):
        return RtuModbus(self.logger)

    async def connect_device(self, device_instance):
        await device_instance.connect_to_modbus_server()


    async def disconnect_device(self, device_instance):
        await device_instance.close_modbus_client()

#############################################################################################