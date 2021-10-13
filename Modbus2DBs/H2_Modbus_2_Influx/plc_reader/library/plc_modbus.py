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

# class IngridModbusCommands(aenum.Enum):
#     _init_           = 'value    register   register_type               modbus_type         access                   uom         count'
    # COMMAND          = auto(),   0,         ModbusRegisterType.HOLDING, ModbusTypes.INT16,  ModbusAccess.WRITE,      'status',   None # HOLDING


class PlcModbus(BaseModbus):

    def __init__(self, logger, variables_dict=None, ip='192.168.0.1', port =502):
        super().__init__(variables_dict=variables_dict, logger=logger)

        self.ip = ip
        self.port = port
        self.ping_interval = utils.get(variables_dict, 'PING_INTERVAL', 60)
        

    def connect(self):
        self.client = ModbusTcpClient(self.ip, self.port, id = self.modbus_id)
        return self.client.connect()

    def disconnect(self):
        return self.client.close()


    def start_pinging_device(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.periodic_ping())


    async def periodic_ping(self):
        while True:
            asyncio.gather(utils.ping(self.ip))
            self.logger.debug(f'PINGING::{self.ip}:{self.port}')
            await asyncio.sleep(self.ping_interval)