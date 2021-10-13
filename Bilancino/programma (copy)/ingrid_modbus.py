# from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusTcpClient
# from pymodbus.client.asynchronous.udp import (AsyncModbusUDPClient as ModbusUdpClient)
# from pymodbus.client.asynchronous import schedulers

import logging
import os
import time
import sys
import traceback
import asyncio
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder

from pymodbus.client.sync import ModbusTcpClient
import library.utils as utils
from library.base_modbus import BaseModbus, ModbusTypes, ModbusAccess, ModbusRegisterType
from library.measurement import Measurement, ModbusMeasurement
import aenum
from enum import Enum, auto


# logging config
# logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


# class IngridModbusCommands(aenum.Enum):
#     _init_           = 'value    register   register_type               modbus_type         access                   uom         count'
# COMMAND          = auto(),   0,         ModbusRegisterType.HOLDING, ModbusTypes.INT16,  ModbusAccess.WRITE,      'status',   None # HOLDING


class IngridModbusMainCommands(Enum):
    WRITE_ODO_SETPOINT = 'write_odo_setpoint'


class IngridModbus(BaseModbus):
    def __init__(self, logger, setpoint_measurement, variables_dict=None):  # passargli un logger, None, dictionary
        super().__init__(variables_dict)
        self.logger = logger
        self.ip = variables_dict["MODBUS_IP"]["value"]
        self.port = utils.parse_int(variables_dict["MODBUS_PORT"]["value"], 1)

        self.setpoint_measurement = setpoint_measurement
        # _, self.odosetpoint_dict = odosetpoint_dict# utils.parse_reading_env(self.get('INGRID_ODO_SETPOINT'))

        # self.id = utils.parse_int(os.getenv('MODBUS_ID', 1), 1)

    def connect(self):
        self.client = ModbusTcpClient(self.ip, self.port)
        return self.client.connect()

    def get_list_command_enums(self):
        return []

    def get_list_command_main_enums(self):
        return [IngridModbusMainCommands]

    async def write_odo_setpoint(self, value):
        if utils.parse_bool(self.get('FEEDBACK_ACTIVATION', default=False), default=False):
            # _, odosetpoint_dict = utils.parse_reading_env(os.getenv('INGRID_ODO_SETPOINT'))

            # await self.connect_to_modbus_server()
            if self.setpoint_measurement is None:
                self.logger.info('-------------------------------------------------------')
                self.logger.info('CANNOT WRITE SETPOINT to value {}. (missing ODORANT_SETPOINT measurement in env variables)'.format(value))
                self.logger.info('-------------------------------------------------------')
            else:
                self.logger.info('-------------------------------------------------------')
                self.logger.info('WRITING. Set point CHANGED to value {}.'.format(value))

                await self.write_value(self.setpoint_measurement.register_number, self.setpoint_measurement.value_type, value, count=self.setpoint_measurement.count)
                # await asyncio.sleep(0.5)
                value = await self.read_value(self.setpoint_measurement.register_number, self.setpoint_measurement.value_type, register_type=self.setpoint_measurement.register_type, count=self.setpoint_measurement.count)

                self.logger.info('READ SET POINT: {}.'.format(value))
                self.logger.info('-------------------------------------------------------')

                # await self.write_value(self.odosetpoint_dict["register"], self.odosetpoint_dict["type"], value)
            # await self.close_modbus_client()

        else:
            self.logger.info('-------------------------------------------------------')
            self.logger.info('FEEDBACK_ACTIVATION is false. Set point NOT CHANGED to value {}'.format(value))
            self.logger.info('-------------------------------------------------------')
