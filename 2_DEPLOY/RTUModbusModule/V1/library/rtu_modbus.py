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

from pymodbus.client.sync import ModbusSerialClient
import library.utils as utils
from library.base_modbus import BaseModbus, ModbusTypes, ModbusAccess, ModbusRegisterType
from library.measurement import Measurement, ModbusMeasurement
import aenum
from enum import Enum, auto


class RtuModbus(BaseModbus):

    def __init__(self, logger, variables_dict=None):
        super().__init__(variables_dict=variables_dict, logger=logger)

        self.port       = self.get('MODBUS_PORT'        , default=  '/dev/ttyUSB0')
        self.stopbits   = int(self.get('MODBUS_STOPBITS'    , default=  1))
        self.bytesize   = int(self.get('MODBUS_BYTESIZE'    , default=  8))
        self.baudrate   = int(self.get('MODBUS_BAUDRATE'    , default=  19200))
        self.timeout    = int(self.get('MODBUS_TIMEOUT'     , default=  1))
        self.method     = self.get('MODBUS_METHOD'      , default=  'rtu')
        self.parity     = self.get('MODBUS_PARITY'      , default=  'N')
        

    def connect(self):
        self.client = ModbusSerialClient(method=self.method, port = self.port, stopbits = self.stopbits, bytesize=self.bytesize,
                            baudrate = self.baudrate, timeout = self.timeout, parity=self.parity)
        return self.client.connect()


    def get_list_command_enums(self):
        return []


    def get_list_command_main_enums(self):
        return []


    def get_command_from_channel(self, channel):
        None