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


class DragoRELE96800Commands(aenum.Enum):
    _init_ = 'value register modbus_type access uom count'
    RELE_1 = auto(), 0, ModbusTypes.COIL, ModbusAccess.READ_WRITE, 'NONE', None
    RELE_2 = auto(), 1, ModbusTypes.COIL, ModbusAccess.READ_WRITE, 'NONE', None
    RELE_3 = auto(), 2, ModbusTypes.COIL, ModbusAccess.READ_WRITE, 'NONE', None
    RELE_4 = auto(), 3, ModbusTypes.COIL, ModbusAccess.READ_WRITE, 'NONE', None

    RELE_DIRECT = auto(), 10, ModbusTypes.UINT16, ModbusAccess.READ_WRITE, 'NONE', None
    

class DragoRELE96800(BaseDrago):
    def __init__(self, variables_dict=None, logger=None):
        super().__init__(variables_dict=variables_dict, logger=logger)


    def get_list_command_enums(self):
        return super().get_list_command_enums() + [DragoRELE96800Commands]


    def get_command_from_channel(self, channel):
        if      channel == 'DO1' or channel == 'RELE1': 
            return DragoRELE96800Commands.RELE_1
        elif    channel == 'DO2' or channel == 'RELE2':  
            return DragoRELE96800Commands.RELE_2
        elif    channel == 'DO3' or channel == 'RELE3':  
            return DragoRELE96800Commands.RELE_3
        elif    channel == 'DO4' or channel == 'RELE4':  
            return DragoRELE96800Commands.RELE_4



if __name__ == "__main__":


    async def main():
        drago = DragoRELE96800({"MODBUS_ID": 2})
        await drago.connect_to_modbus_server()

        # print("Coils 1: FALSE (write)", drago.client.write_coil(0, False, unit=2))
        # print("Coils 3: TRUE (write)", drago.client.write_coil(2, True, unit=2))

        # print("Coils 1: ", drago.client.read_coils(0, 1, unit=2).bits)
        # print("Coils 2: ", drago.client.read_coils(1, 1, unit=2).bits)
        # print("Coils 3: ", drago.client.read_coils(2, 1, unit=2).bits)
        # print("Coils 4: ", drago.client.read_coils(3, 1, unit=2).bits)

        # print("Coils 1: TRUE (write)", drago.client.write_coil(0, True, unit=2))
        # print("Coils 3: FALSE (write)", drago.client.write_coil(2, False, unit=2))

        # print("Coils 1: ", drago.client.read_coils(0, 1, unit=2).bits)
        # print("Coils 2: ", drago.client.read_coils(1, 1, unit=2).bits)
        # print("Coils 3: ", drago.client.read_coils(2, 1, unit=2).bits)
        # print("Coils 4: ", drago.client.read_coils(3, 1, unit=2).bits)
        
        print("Rele1 : FALSE (write)", await drago.execute_command_write(DragoRELE96800Commands.RELE_1, False))
        print("Rele3 : TRUE (write)", await drago.execute_command_write(DragoRELE96800Commands.RELE_3, True))

        print("Rele1 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_1))
        print("Rele2 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_2))
        print("Rele3 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_3))
        print("Rele4 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_4))
        print("RELE_DIRECT : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_DIRECT))

        print("Rele1 : TRUE (write)", await drago.execute_command_write(DragoRELE96800Commands.RELE_1, True))
        print("Rele3 : FALSE (write)", await drago.execute_command_write(DragoRELE96800Commands.RELE_3, False))

        print("Rele1 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_1))
        print("Rele2 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_2))
        print("Rele3 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_3))
        print("Rele4 : ", await drago.execute_command_read(DragoRELE96800Commands.RELE_4))
        
        for e in drago.get_list_command_enums():
            for i in e:
                print(f"Read {i} : ", await drago.execute_command_read(i))


    asyncio.run(main())


