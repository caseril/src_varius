import logging
import os
import time
import sys
import traceback
import asyncio
import library.utils as utils
from abc import ABC, abstractmethod
import aenum
from library.base_modbus import BaseModbus, ModbusTypes, ModbusAccess
from enum import Enum, auto
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusSerialClient

# logging config
# logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# logging.basicConfig(filename='log', filemode='w', format='%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
# logging.getLogger(__name__).setLevel(logging.DEBUG)
# logging.getLogger("pymodbus").setLevel(logging.CRITICAL)
# logging.getLogger("azure.iot").setLevel(logging.CRITICAL)
# logging.getLogger("azure").setLevel(logging.CRITICAL)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class IdentifiersCommands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'
    DEVICE_IDENTIFIER = auto(), 3000, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    HARDWARE_VERSION = auto(), 3001, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    RFID_IDENTIFIER = auto(), 3004, ModbusTypes.STRING, ModbusAccess.READ, 'NONE', 8
    FIRMWARE_VERSION = auto(), 3028, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    POINT_OF_MEASURING = auto(), 5150, ModbusTypes.STRING, ModbusAccess.READ_WRITE, 'NONE', 8


class DIPCommands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'
    CURRENT_DIP_SWITCHES = auto(), 100, ModbusTypes.UINT32, ModbusAccess.READ, 'NONE', None
    CURRENT_PC_CONFIG = auto(), 102, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None


class CommonCommands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'
    MODBUS_PC_UNIT_ID = auto(), 5009, ModbusTypes.UINT16, ModbusAccess.READ_WRITE, 'NONE', None
    MODBUS_PC_BAUDRATE = auto(), 5010, ModbusTypes.UINT16, ModbusAccess.READ_WRITE, 'NONE', None
    MODBUS_PC_PARITY_STOPBITS = auto(), 5011, ModbusTypes.UINT16, ModbusAccess.READ_WRITE, 'NONE', None
    MODBUS_PC_RESPONSE_DELAY = auto(), 5012, ModbusTypes.UINT16, ModbusAccess.READ_WRITE, 'NONE', None
    
    MODBUS_DIP_UNIT_ID = auto(), 5019, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    MODBUS_DIP_PARITY_STOPBITS = auto(), 5020, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    MODBUS_DIP_BAUDRATE = auto(), 5021, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    MODBUS_DIP_RESPONSE_DELAY = auto(), 5022, ModbusTypes.UINT16, ModbusAccess.READ, 'NONE', None
    
    SAVE_SETTINGS = auto(), 8212, ModbusTypes.UINT16, ModbusAccess.WRITE, 'NONE', None



class BaseDrago(BaseModbus):
    def __init__(self, variables_dict=None, logger=None):
        super().__init__(variables_dict=variables_dict, logger=logger)
        # self.modbus_id = utils.parse_int(self.get('MODBUS_ID', 1), 1)

        self.modbus_port = self.get('MODBUS_PORT', '/dev/ttyUSB0')
        self.modbus_stopbits = utils.parse_int(self.get('MODBUS_STOPBITS', 1), 1)
        self.modbus_bytesize = utils.parse_int(self.get('MODBUS_BYTESIZE', 8), 8)
        self.modbus_baudrate = utils.parse_int(self.get('MODBUS_BAUDRATE', 19200), 19200)
        self.modbus_timeout = utils.parse_int(self.get('MODBUS_TIMEOUT', 1), 1)
        self.modbus_method = self.get('MODBUS_METHOD', 'rtu')
        self.modbus_parity = self.get('MODBUS_PARITY', 'E')


    def get_list_command_main_enums(self):
        return []


    def get_list_command_enums(self):
        return [IdentifiersCommands, DIPCommands, CommonCommands]


    @abstractmethod
    def get_command_from_channel(self, channel):
        pass


    def connect(self):
        self.client = ModbusSerialClient(port=self.modbus_port,
                        stopbits=self.modbus_stopbits,
                        bytesize=self.modbus_bytesize,
                        parity=self.modbus_parity,
                        baudrate=self.modbus_baudrate,
                        timeout=self.modbus_timeout,
                        method=self.modbus_method)
        return self.client.connect()

