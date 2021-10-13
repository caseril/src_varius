import logging
import os
import time
import sys
import traceback
import asyncio
import library.utils as utils
import aenum
from enum import Enum, auto
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusSerialClient
from library.base_drago import ModbusTypes, IdentifiersCommands, DIPCommands, CommonCommands, BaseDrago, ModbusAccess

# logging config
# logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))



class DragoAI96100Commands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'
    VALUE_0_20UA = auto(), 0, ModbusTypes.INT16, ModbusAccess.READ, 'uA', None
    VALUE_0_20MA = auto(), 1, ModbusTypes.INT16, ModbusAccess.READ, 'mA', None
    STATUS = auto(), 4, ModbusTypes.INT16, ModbusAccess.READ, 'NONE', None
    VALUE_SCALED = auto(), 50, ModbusTypes.FLOAT32, ModbusAccess.READ, 'NONE', None
    SCALE_IN_MIN = auto(), 2006, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'mA', None
    SCALE_IN_MAX = auto(), 2008, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'mA', None
    SCALE_OUT_MIN = auto(), 2010, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'NONE', None
    SCALE_OUT_MAX = auto(), 2012, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'NONE', None
    CURRENT_VOLTAGE_DIP_MODE = auto(), 2512, ModbusTypes.INT16, ModbusAccess.READ, 'NONE', None


class DragoAI96100(BaseDrago):

    def __init__(self, variables_dict=None, logger=None):
        super().__init__(variables_dict=variables_dict, logger=logger)
        # self.setup_scale()


    def get_list_command_enums(self):
        return super().get_list_command_enums() + [DragoAI96100Commands]


    async def setup_scale(self):
        scale_in_min = utils.parse_float(self.get('ANALOG_SCALE_IN_MIN', default=4), default=4)
        scale_in_max = utils.parse_float(self.get('ANALOG_SCALE_IN_MAX', default=20), default=20)
        scale_out_min = utils.parse_float(self.get('ANALOG_SCALE_OUT_MIN', default=4), default=4)
        scale_out_max = utils.parse_float(self.get('ANALOG_SCALE_OUT_MAX', default=20), default=20)

        await self.execute_command_write(DragoAI96100Commands.SCALE_IN_MIN, scale_in_min)
        await self.execute_command_write(DragoAI96100Commands.SCALE_IN_MAX, scale_in_max)
        await self.execute_command_write(DragoAI96100Commands.SCALE_OUT_MIN, scale_out_min)
        await self.execute_command_write(DragoAI96100Commands.SCALE_OUT_MAX, scale_out_max)


    def get_command_from_channel(self, channel):
        if      channel == 'AI1': 
            return DragoAI96100Commands.VALUE_0_20MA




if __name__ == "__main__":

    async def main():
        drago = DragoAI96100({"MODBUS_ID": 1})
        await drago.connect_to_modbus_server()
        await drago.setup_scale()

        print(f"Read {DragoAI96100Commands.VALUE_SCALED} : ", await drago.execute_command_read(DragoAI96100Commands.VALUE_SCALED))

        for e in drago.get_list_command_enums():
            for i in e:
                print(f"Read {i} : ", await drago.execute_command_read(i))


    asyncio.run(main())

