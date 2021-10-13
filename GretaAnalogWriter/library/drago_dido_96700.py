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

# client = ModbusSerialClient(port='/dev/ttyS1',
#                         stopbits=1,
#                         bytesize=8,
#                         parity='E',
#                         baudrate=19200,
#                         timeout=1,
#                         method='rtu')
# client.connect()

class DragoDIDO96700Commands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'
    DIGITAL_IO_1 = auto(), 0, ModbusTypes.COIL, ModbusAccess.READ_WRITE, None, 1
    DIGITAL_IO_2 = auto(), 1, ModbusTypes.COIL, ModbusAccess.READ_WRITE, None, 1
    DIGITAL_IO_3 = auto(), 2, ModbusTypes.COIL, ModbusAccess.READ_WRITE, None, 1
    DIGITAL_IO_4 = auto(), 3, ModbusTypes.COIL, ModbusAccess.READ_WRITE, None, 1

    DIGITAL_IO_DIRECT = auto(), 10, ModbusTypes.UINT16, ModbusAccess.READ_WRITE, None, None

    OPERATING_MODE_CH1 = auto(), 2000, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: INPUT / 16: OUTPUT
    INPUT_LEVEL_CH1 = auto(), 2001, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 5V / 1: 12V / 2: 24V
    PULSE_WIDTH_CH1 = auto(), 2002, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 300ms
    CONTACT_TYPE_CH1 = auto(), 2011, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: NO / 1: NC
    MIN_ACTIVATION_TYPE_CH1 = auto(), 2012, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF 
    MAX_ACTIVATION_TYPE_CH1 = auto(), 2013, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF
    ON_DELAY_CH1 = auto(), 2014, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    OFF_DELAY_CH1 = auto(), 2015, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    INITIAL_STATE_CH1 = auto(), 2016, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF / 1: ON

    OPERATING_MODE_CH2 = auto(), 2100, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: INPUT / 16: OUTPUT
    INPUT_LEVEL_CH2 = auto(), 2101, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 5V / 1: 12V / 2: 24V
    PULSE_WIDTH_CH2 = auto(), 2102, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 300ms
    CONTACT_TYPE_CH2 = auto(), 2111, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: NO / 1: NC
    MIN_ACTIVATION_TYPE_CH2 = auto(), 2112, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF 
    MAX_ACTIVATION_TYPE_CH2 = auto(), 2113, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF
    ON_DELAY_CH2 = auto(), 2114, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    OFF_DELAY_CH2 = auto(), 2115, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    INITIAL_STATE_CH2 = auto(), 2116, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF / 1: ON

    OPERATING_MODE_CH3 = auto(), 2200, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: INPUT / 16: OUTPUT
    INPUT_LEVEL_CH3 = auto(), 2201, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 5V / 1: 12V / 2: 24V
    PULSE_WIDTH_CH3 = auto(), 2202, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 300ms
    CONTACT_TYPE_CH3 = auto(), 2211, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: NO / 1: NC
    MIN_ACTIVATION_TYPE_CH3 = auto(), 2212, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF 
    MAX_ACTIVATION_TYPE_CH3 = auto(), 2213, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF
    ON_DELAY_CH3 = auto(), 2214, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    OFF_DELAY_CH3 = auto(), 2215, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    INITIAL_STATE_CH3 = auto(), 2216, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF / 1: ON

    OPERATING_MODE_CH4 = auto(), 2300, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: INPUT / 16: OUTPUT
    INPUT_LEVEL_CH4 = auto(), 2301, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 5V / 1: 12V / 2: 24V
    PULSE_WIDTH_CH4 = auto(), 2302, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: 300ms
    CONTACT_TYPE_CH4 = auto(), 2311, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: NO / 1: NC
    MIN_ACTIVATION_TYPE_CH4 = auto(), 2312, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF 
    MAX_ACTIVATION_TYPE_CH4 = auto(), 2313, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF
    ON_DELAY_CH4 = auto(), 2314, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    OFF_DELAY_CH4 = auto(), 2315, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: IMMEDIATE
    INITIAL_STATE_CH4 = auto(), 2316, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'NONE', None # 0: OFF / 1: ON
    

class DragoDIDO96700(BaseDrago):
    def __init__(self, variables_dict=None, logger=None):
        super().__init__(variables_dict=variables_dict, logger=logger)


    def get_list_command_enums(self):
        return super().get_list_command_enums() + [DragoDIDO96700Commands]


    def get_command_from_channel(self, channel):
        if      channel == 'DO1' or channel == "DI1": 
            return DragoDIDO96700Commands.DIGITAL_IO_1
        elif    channel == 'DO2' or channel == "DI2": 
            return DragoDIDO96700Commands.DIGITAL_IO_2
        elif    channel == 'DO3' or channel == "DI3": 
            return DragoDIDO96700Commands.DIGITAL_IO_3
        elif    channel == 'DO4' or channel == "DI4": 
            return DragoDIDO96700Commands.DIGITAL_IO_4


    async def setup_config_for_greta_photovoltaic(self):
        commands_dict = {}

        commands_dict[DragoDIDO96700Commands.OPERATING_MODE_CH1]    = 0 # DI
        commands_dict[DragoDIDO96700Commands.INPUT_LEVEL_CH1]       = 2 # 12/24 v

        commands_dict[DragoDIDO96700Commands.OPERATING_MODE_CH2]    = 16 # DO
        commands_dict[DragoDIDO96700Commands.CONTACT_TYPE_CH2]      = 0 # NO
        commands_dict[DragoDIDO96700Commands.INITIAL_STATE_CH2]     = 1 # ON AT START
        commands_dict[DragoDIDO96700Commands.DIGITAL_IO_2]          = 1 # START CHANNEL 2
        
        # commands_dict[CommonCommands.MODBUS_PC_UNIT_ID]  = 1 

        await self.write_configuration(commands_dict)






if __name__ == "__main__":


    async def main():
        drago = DragoDIDO96700({"MODBUS_ID": 1})
        await drago.connect_to_modbus_server()

        print("io_1 : FALSE (write)", await drago.execute_command_write(DragoDIDO96700Commands.DIGITAL_IO_1, False))
        print("io_3 : TRUE (write)", await drago.execute_command_write(DragoDIDO96700Commands.DIGITAL_IO_3, True))

        print("io_1 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_1))
        print("io_2 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_2))
        print("io_3 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_3))
        print("io_4 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_4))
        print("DIGITAL_IO_DIRECT : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_DIRECT))

        print("io_1 : TRUE (write)", await drago.execute_command_write(DragoDIDO96700Commands.DIGITAL_IO_1, True))
        print("io_3 : FALSE (write)", await drago.execute_command_write(DragoDIDO96700Commands.DIGITAL_IO_3, False))

        print("io_1 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_1))
        print("io_2 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_2))
        print("io_3 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_3))
        print("io_4 : ", await drago.execute_command_read(DragoDIDO96700Commands.DIGITAL_IO_4))
        
        for e in drago.get_list_command_enums():
            for i in e:
                print(f"Read {i} : ", await drago.execute_command_read(i))


    asyncio.run(main())


