
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
from library.measurement import Measurement, ModbusMeasurement
import library.utils as utils

from library.drago_aiao_96400   import DragoAIAO96400, DragoAIAO96400Commands
from library.drago_ai_96100     import DragoAI96100, DragoAI96100Commands
from library.drago_dido_96700   import DragoDIDO96700, DragoDIDO96700Commands
from library.drago_rele_96800   import DragoRELE96800, DragoRELE96800Commands

class DoorModuleClass(BaseIotHubReaderModuleClient):

    MACHINE_TYPE = "SECURITY"

    def __init__(self):
        super().__init__(self.MACHINE_TYPE, None, None)

        measurement_list = utils.get_all_measurement_list(DoorModuleClass.MACHINE_TYPE, os.environ)
        config_measurement_list = utils.get_config_measurement_list(DoorModuleClass.MACHINE_TYPE, os.environ, logger=self.logger)

        self.measurement_list           = measurement_list
        self.config_measurement_list    = config_measurement_list

        self.device_type                = utils.get(self.variables_dict, 'DEVICE_TYPE', default='DragoAIAO96400')
        

    def _get_device_(self):
        if self.device_type == 'DragoAI96100':
            device_class = DragoAI96100

        elif self.device_type == 'DragoAIAO96400':
            device_class = DragoAIAO96400

        elif self.device_type == 'DragoDIDO96700':
            device_class = DragoDIDO96700

        elif self.device_type == 'DragoRELE96800':
            device_class = DragoRELE96800

        else:  
            self.logger.critical(f'DoorModuleClass::_get_device_::device_type {self.device_type} not recognized')
            return None

        return device_class(variables_dict=self.variables_dict, logger=self.logger)



    async def init_device_instance(self):
        return self._get_device_()
        # return DragoDIDO96700(os.environ, logger=self.logger)        


    async def connect_device(self, device_instance):
        await device_instance.connect_to_modbus_server()


    async def disconnect_device(self, device_instance):
        await device_instance.close_modbus_client()
