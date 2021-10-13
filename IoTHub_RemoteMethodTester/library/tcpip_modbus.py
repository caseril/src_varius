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


class TcpIpModbus(BaseModbus):

    def __init__(self, logger, setpoint_measurement, variables_dict=None):
        super().__init__(variables_dict=variables_dict, logger=logger)

        self.ip = self.get('MODBUS_IP', default='192.168.0.1')
        self.port = utils.parse_int(self.get('MODBUS_PORT'), default=502)

    def connect(self):
        self.client = ModbusTcpClient(self.ip, self.port)
        return self.client.connect()

    def get_list_command_enums(self):
        return []

    def get_command_from_channel(self, channel):
        None