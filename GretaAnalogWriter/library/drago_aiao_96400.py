import logging
import os
import time
import sys
import traceback
import asyncio
# import library.utils as utils
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



class DragoAIAO96400Commands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'

    VALUE_AI_1  = auto(), 0,  ModbusTypes.INT16, ModbusAccess.READ,       'uA',     None
    VALUE_AI_2  = auto(), 1,  ModbusTypes.INT16, ModbusAccess.READ,       'uA',     None
    VALUE_AO_1  = auto(), 2,  ModbusTypes.INT16, ModbusAccess.READ_WRITE, 'uA',     None
    VALUE_AO_2  = auto(), 3,  ModbusTypes.INT16, ModbusAccess.READ_WRITE, 'uA',     None
    STATUS      = auto(), 4,  ModbusTypes.UINT16, ModbusAccess.READ,       'NONE',   None

    DISCRETE_IO = auto(), 10, ModbusTypes.INT16, ModbusAccess.READ_WRITE, 'NONE',   None

    VALUE_SCALED_AI_1 = auto(), 50, ModbusTypes.FLOAT32, ModbusAccess.READ,         'NONE', None
    VALUE_SCALED_AI_2 = auto(), 52, ModbusTypes.FLOAT32, ModbusAccess.READ,         'NONE', None
    VALUE_SCALED_AO_1 = auto(), 54, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE,   'NONE', None
    VALUE_SCALED_AO_2 = auto(), 56, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE,   'NONE', None

    INPUT_MODE_AI_1     = auto(), 2000, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'mA', None
    INPUT_FILTER_AI_1   = auto(), 2001, ModbusTypes.INT16,   ModbusAccess.READ_WRITE, 'mA', None
    SCALE_IN_MIN_AI_1   = auto(), 2002, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'uA', None
    SCALE_IN_MAX_AI_1   = auto(), 2004, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'uA', None
    SCALE_OUT_MIN_AI_1  = auto(), 2006, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'NONE', None
    SCALE_OUT_MAX_AI_1  = auto(), 2008, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'NONE', None
    INPUT_LEVEL_AI_1    = auto(), 2030, ModbusTypes.INT16,   ModbusAccess.READ_WRITE, 'NONE', None

    INPUT_MODE_AI_2     = auto(), 2100, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'mA', None
    INPUT_FILTER_AI_2   = auto(), 2101, ModbusTypes.INT16,   ModbusAccess.READ_WRITE, 'mA', None
    SCALE_IN_MIN_AI_2   = auto(), 2102, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'uA', None
    SCALE_IN_MAX_AI_2   = auto(), 2104, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'uA', None
    SCALE_OUT_MIN_AI_2  = auto(), 2106, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'NONE', None
    SCALE_OUT_MAX_AI_2  = auto(), 2108, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'NONE', None
    INPUT_LEVEL_AI_2    = auto(), 2130, ModbusTypes.INT16,   ModbusAccess.READ_WRITE, 'mA', None

    OUTPUT_MODE_AO_1    = auto(), 2400, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'mA', None
    OUTPUT_TIMEOUT_AO_1 = auto(), 2401, ModbusTypes.INT16,   ModbusAccess.READ_WRITE, 'mA', None
    OUTPUT_INIT_AO_1    = auto(), 2402, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'uA', None

    OUTPUT_MODE_AO_2    = auto(), 2500, ModbusTypes.UINT16,  ModbusAccess.READ_WRITE, 'mA', None
    OUTPUT_TIMEOUT_AO_2 = auto(), 2501, ModbusTypes.INT16,   ModbusAccess.READ_WRITE, 'mA', None
    OUTPUT_INIT_AO_2    = auto(), 2502, ModbusTypes.FLOAT32, ModbusAccess.READ_WRITE, 'uA', None

    DIGITAL_IO_1        = auto(), 0, ModbusTypes.COIL, ModbusAccess.READ_WRITE, None, 1
    DIGITAL_IO_2        = auto(), 1, ModbusTypes.COIL, ModbusAccess.READ_WRITE, None, 1
    

class DragoAIAO96400(BaseDrago):

    def __init__(self, variables_dict=None, logger=None):
        super().__init__(variables_dict=variables_dict, logger=logger)
        # self.setup_scale()


    def get_list_command_enums(self):
        return super().get_list_command_enums() + [DragoAIAO96400Commands]


    # async def setup_scale(self):
    #     scale_in_min = utils.parse_float(self.get('ANALOG_SCALE_IN_MIN', default=4), default=4)
    #     scale_in_max = utils.parse_float(self.get('ANALOG_SCALE_IN_MAX', default=20), default=20)
    #     scale_out_min = utils.parse_float(self.get('ANALOG_SCALE_OUT_MIN', default=4), default=4)
    #     scale_out_max = utils.parse_float(self.get('ANALOG_SCALE_OUT_MAX', default=20), default=20)

    #     await self.execute_command_write(DragoAIAO96400Commands.SCALE_IN_MIN, scale_in_min)
    #     await self.execute_command_write(DragoAIAO96400Commands.SCALE_IN_MAX, scale_in_max)
    #     await self.execute_command_write(DragoAIAO96400Commands.SCALE_OUT_MIN, scale_out_min)
    #     await self.execute_command_write(DragoAIAO96400Commands.SCALE_OUT_MAX, scale_out_max)


    async def setup_config_for_greta(self):
        commands_dict = {}
    
        commands_dict[DragoAIAO96400Commands.INPUT_MODE_AI_1]       = 512 # digital input mode
        commands_dict[DragoAIAO96400Commands.INPUT_LEVEL_AI_1]      = 1 # 12/24 v
        
        commands_dict[DragoAIAO96400Commands.OUTPUT_MODE_AO_1]      = 0 # 0-20000 Ma
        commands_dict[DragoAIAO96400Commands.OUTPUT_TIMEOUT_AO_1]   = 0 # timeout
        commands_dict[DragoAIAO96400Commands.OUTPUT_INIT_AO_1]      = 1 # 12/24 v

        commands_dict[DragoAIAO96400Commands.OUTPUT_MODE_AO_2]      = 0 # 0-20000 Ma
        commands_dict[DragoAIAO96400Commands.OUTPUT_TIMEOUT_AO_2]   = 0 # timeout
        commands_dict[DragoAIAO96400Commands.OUTPUT_INIT_AO_2]      = 1 # 12/24 v

        # commands_dict[CommonCommands.MODBUS_PC_UNIT_ID]  = 10 # 12/24 v

        await self.write_configuration(commands_dict)


    async def setup_config_for_test(self):
        commands_dict = {}
        commands_dict[DragoAIAO96400Commands.INPUT_MODE_AI_2]   = 0 # 0-20mA
        await self.write_configuration(commands_dict)


    async def get_config_for_greta(self):
        commands_list = [
            DragoAIAO96400Commands.INPUT_MODE_AI_1, \
            DragoAIAO96400Commands.INPUT_LEVEL_AI_1, \
            DragoAIAO96400Commands.OUTPUT_MODE_AO_1, \
            DragoAIAO96400Commands.OUTPUT_INIT_AO_1, \
            DragoAIAO96400Commands.OUTPUT_TIMEOUT_AO_1, \
            DragoAIAO96400Commands.OUTPUT_MODE_AO_2, \
            DragoAIAO96400Commands.OUTPUT_INIT_AO_2, \
            DragoAIAO96400Commands.OUTPUT_TIMEOUT_AO_2
        ] 

        results_dict = {}
        for command in commands_list:
            value, uom = await self.execute_command_read(command)
            results_dict[command] = value
        
        return results_dict


    def get_command_from_channel(self, channel):
        if      channel == 'AI1': 
            return DragoAIAO96400Commands.VALUE_AI_1
        elif    channel == 'AI2': 
            return DragoAIAO96400Commands.VALUE_AI_2
        elif    channel == 'AO1': 
            return DragoAIAO96400Commands.VALUE_AO_1
        elif    channel == 'AO2': 
            return DragoAIAO96400Commands.VALUE_AO_2
        elif    channel == 'DO1' or channel == "DI1": 
            return DragoAIAO96400Commands.DIGITAL_IO_1
        elif    channel == 'DO2' or channel == "DI2": 
            return DragoAIAO96400Commands.DIGITAL_IO_2


if __name__ == "__main__":
    
    sys.path.append('./')
    sys.path.append('./library')

    async def main():
        drago = DragoAIAO96400({"MODBUS_ID": 3})
        # drago = DragoAIAO96400({"MODBUS_ID": 4})
        
        await drago.connect_to_modbus_server()

        drago.modbus_id = 3
        await drago.execute_command_write(DragoAIAO96400Commands.INPUT_MODE_AI_1, 768) # DO
        await drago.execute_command_write(DragoAIAO96400Commands.INPUT_LEVEL_AI_1, 1) # 12/24V INPUT # useless ? 

        drago.modbus_id = 4
        await drago.execute_command_write(DragoAIAO96400Commands.INPUT_MODE_AI_1, 512) # DI
        await drago.execute_command_write(DragoAIAO96400Commands.INPUT_LEVEL_AI_1, 1) # 12/24V INPUT

        for i in range(100):
            if i % 5 == 0:
                drago.modbus_id = 3
                print('Read drago DISCRETE_IO: ', await drago.execute_command_read(DragoAIAO96400Commands.DISCRETE_IO))
                if i % 10 == 0:
                    await drago.execute_command_write(DragoAIAO96400Commands.DISCRETE_IO, 3)
                else:
                    await drago.execute_command_write(DragoAIAO96400Commands.DISCRETE_IO, 3)

            drago.modbus_id = 4
            print('Read drago: ', await drago.execute_command_read(DragoAIAO96400Commands.VALUE_AI_1))
            await asyncio.sleep(1)


        # await drago.setup_scale()

        # print(f"Read {DragoAI96100Commands.VALUE_SCALED} : ", await drago.execute_command_read(DragoAI96100Commands.VALUE_SCALED))

        # for e in drago.get_list_command_enums():
        #     for i in e:
        #         print(f"Read {i} : ", await drago.execute_command_read(i))


    asyncio.run(main())

