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

    def __init__(self, logger, id, port, stopbits, bytesize, baudrate, timeout, method, parity, byteorder, wordorder, variables_dict=None):
        super().__init__(variables_dict=variables_dict, logger=logger)

        self.modbus_id = id
        self.modbus_port = port
        self.modbus_stopbits= stopbits
        self.modbus_bytesize = bytesize
        self.modbus_baudrate = baudrate
        self.modbus_timeout = timeout
        self.modbus_method = method
        self.modbus_parity = parity
        self.modbus_byteorder = Endian.Little if byteorder.lower() == 'little' else Endian.Big
        self.modbus_wordorder = Endian.Little if wordorder.lower() == 'little' else Endian.Big
        

    def connect(self):
        self.client = ModbusClient(method= self.modbus_method, port = self.modbus_port, 
                                    timeout = self.modbus_timeout, baudrate = self.modbus_baudrate, 
                                    stopbits = self.modbus_stopbits, bytesize = self.modbus_bytesize,
                                    parity=self.modbus_parity)
        return self.client.connect()

    def disconnect(self):
        return self.client.close()
