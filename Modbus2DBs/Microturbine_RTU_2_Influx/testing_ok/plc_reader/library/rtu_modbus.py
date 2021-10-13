import logging
import os
import time
import sys
import traceback
import asyncio
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.transaction import ModbusRtuFramer as ModbusFramer
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import library.utils as utils
from library.base_modbus import BaseModbus, ModbusTypes, ModbusAccess, ModbusRegisterType
from library.measurement import Measurement, ModbusMeasurement
import aenum
from enum import Enum, auto

# class IngridModbusCommands(aenum.Enum):
#     _init_           = 'value    register   register_type               modbus_type         access                   uom         count'
    # COMMAND          = auto(),   0,         ModbusRegisterType.HOLDING, ModbusTypes.INT16,  ModbusAccess.WRITE,      'status',   None # HOLDING


class RtuModbus(BaseModbus):

    def __init__(self, logger, port, stopbits, bytesize, baudrate, timeout, method, parity, variables_dict=None):
        super().__init__(variables_dict=variables_dict, logger=logger)

        self.port = port
        self.stopbits= stopbits
        self.bytesize = bytesize
        self.baudrate = baudrate
        self.timeout = timeout
        self.method = method
        self.parity = parity
        

    def connect(self):
        self.client = ModbusClient(method= self.method, port = self.port, 
                                    timeout = self.timeout, baudrate = self.baudrate, 
                                    stopbits = self.stopbits, bytesize = self.bytesize,
                                    parity=self.parity)
        return self.client.connect()

    def disconnect(self):
        return self.client.close()
