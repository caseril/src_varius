import logging
import os
import time
import sys
import traceback
import asyncio
import library.utils as utils
import aenum
from abc import ABC, abstractmethod
from enum import Enum, auto
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusSerialClient

# logging config
# logging.basicConfig(filename='log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# self.logger.addHandler(logging.StreamHandler(sys.stdout))

# logging.basicConfig(filename='log', filemode='w', format='%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
# logging.getLogger(__name__).setLevel(logging.DEBUG)
# logging.getLogger("pymodbus").setLevel(logging.CRITICAL)
# logging.getLogger("azure.iot").setLevel(logging.CRITICAL)
# logging.getLogger("azure").setLevel(logging.CRITICAL)
# self.logger.addHandler(logging.StreamHandler(sys.stdout))


class ModbusTypes(Enum):
    COIL = auto()
    BOOL1 = auto()
    INT8HIGH = auto()
    INT8LOW = auto()
    INT16 = auto()
    INT32 = auto()
    INT64 = auto()
    UINT8HIGH = auto()
    UINT8LOW = auto()
    UINT16 = auto()
    UINT32 = auto()
    UINT64 = auto()
    FLOAT16 = auto()
    FLOAT32 = auto()
    FLOAT64 = auto()
    STRING = auto() # 
    BIT0 = auto() # num & 00000001
    BIT1 = auto() # num & 00000010
    BIT2 = auto() # num & 00000100
    BIT3 = auto() # num & 00001000
    BIT4 = auto() # num & 00010000
    BIT5 = auto() # num & 00100000
    BIT6 = auto() # num & 01000000
    BIT7 = auto() # num & 10000000
    BIT0HIGH = auto() # num & 00000001
    BIT1HIGH = auto() # num & 00000010
    BIT2HIGH = auto() # num & 00000100
    BIT3HIGH = auto() # num & 00001000
    BIT4HIGH = auto() # num & 00010000
    BIT5HIGH = auto() # num & 00100000
    BIT6HIGH = auto() # num & 01000000
    BIT7HIGH = auto() # num & 10000000
    BIT0LOW = auto() # num & 00000001
    BIT1LOW = auto() # num & 00000010
    BIT2LOW = auto() # num & 00000100
    BIT3LOW = auto() # num & 00001000
    BIT4LOW = auto() # num & 00010000
    BIT5LOW = auto() # num & 00100000
    BIT6LOW = auto() # num & 01000000
    BIT7LOW = auto() # num & 10000000


class ModbusAccess(Enum):
    READ = auto()
    WRITE = auto()
    READ_WRITE = auto()


class ModbusRegisterType(Enum):
    COIL = auto()
    INPUT = auto()
    HOLDING = auto()


class BaseModbus(ABC):
    def __init__(self, variables_dict=None, logger=None):
        self.logger = logger
        if self.logger is None:
            self.logger = logging.getLogger()
        self.variables_dict = utils.merge_dicts_priority(variables_dict, os.environ) #  os.environ if variables_dict is None else variables_dict
        self.client = None


    def is_simulator(self):
        return utils.parse_bool(self.get("SIMULATOR", default=False), default=False)


    def is_enabled(self):
        return utils.parse_bool(self.get("ENABLED", default=True), default=True)


    def get(self, key, default=None):
        return utils.get(self.variables_dict, key, default=default)

    async def execute_command_str(self, command_str):
        self.logger.info(f'execute_command_str::start')
        # FIRST: TRY TO RUN AS MAIN COMMAND
        for commands_enum in self.get_list_command_main_enums():
            if command_str in [k.name for k in commands_enum]: 
                command = commands_enum[command_str]
                return await self.execute_command_main(command)

        # SECOND: TRY TO RUN AS READ COMMAND
        return await self.execute_command_str_read(command_str)


    async def execute_command_str_read(self, command_str):
        self.logger.info(f'execute_command_str_read::start')
        for commands_enum in self.get_list_command_enums():
            if command_str in [k.name for k in commands_enum]: 
                command = commands_enum[command_str]
                return await self.execute_command_read(command)
        return None, None
        

    async def execute_command_str_write(self, command_str, value):
        self.logger.info(f'execute_command_str_write::start')
        for commands_enum in self.get_list_command_enums():
            if command_str in [k.name for k in commands_enum]: 
                command = commands_enum[command_str]
                return await self.execute_command_write(command, value)
        return None, None


    async def execute_command_str_main(self, command_str):
        self.logger.info(f'execute_command_str_main::start')
        for commands_enum in self.get_list_command_main_enums():
            if command_str in [k.name for k in commands_enum]: 
                command = commands_enum[command_str]
                return await self.execute_command_main(command)
        return None, None


    async def execute_command_read(self, command):
        self.logger.info(f'execute_command_read::start')
        if command.access == ModbusAccess.READ or command.access == ModbusAccess.READ_WRITE:
            register_type = self._get_register_type_from_command_(command)
            value = await self.read_value(command.register, command.modbus_type.name, register_type=register_type, count=command.count)
            return self._read_decode_(command, value), command.uom
        return None, None
        

    async def execute_command_write(self, command, value):
        self.logger.info(f'execute_command_write::start')
        if command.access == ModbusAccess.WRITE or command.access == ModbusAccess.READ_WRITE:
            return await self.write_value(command.register, command.modbus_type.name, self._write_encode_(command, value)), command.uom
        return None, None
        

    async def execute_command_main(self, command):
        self.logger.info(f'execute_command_main::start')
        # RUN FUNCTION AS COMMAND VALUE NAME
        return await getattr(self, command.value)()


    def _get_register_type_from_command_(self, command):
        if 'register_type' in vars(command):
            return command.register_type
        else:
            return ModbusRegisterType.HOLDING # default are HOLDING

    
    async def write_configuration(self, commands_dict):
        for command, value in commands_dict.items():
            await self.execute_command_write(command, value)


    @abstractmethod
    def connect(self):
        pass 

    @abstractmethod
    def disconnect(self):
        pass 


    def _read_decode_(self, command, value):
        return value 


    def _write_encode_(self, command, value):
        return value 


    async def connect_to_modbus_server(self):
        if not self.is_simulator():
            self.logger.debug(f'connect_to_modbus_server::start') 

            if(await utils.run_and_try_if_true_async(self.connect, 10, 0.1)):
                self.logger.info(f'connect_to_modbus_server::connected')
            else:
                self.logger.critical(f'connect_to_modbus_server::failed_to_connect')
        else:
            self.logger.debug(f'connect_to_modbus_server::simulator') 


    async def close_modbus_client(self):
        if not self.is_simulator():
            await utils.run_and_try_async(self.disconnect, 3, 0.1)
            self.logger.info(f'close_modbus_client::disconnected') 
        else:
            self.logger.debug(f'close_modbus_client::simulator::start') 


    def read_holding_registers(self, register, count):
        if not self.is_simulator():
            registers = self.client.read_holding_registers(register, count, unit=self.modbus_id).registers
            self.logger.debug(f'read_holding_registers::register::{register}::count::{count}::values::{registers}')
            # self.logger.debug("READ HOLDING: number: {}, Count: {}, values: {}".format(register, count, registers))
            return registers
        else:
            self.logger.debug(f'read_holding_registers::simulator') 


    def read_input_registers(self, register, count):
        if not self.is_simulator():
            registers = self.client.read_input_registers(register, count, unit=self.modbus_id).registers
            self.logger.debug(f'read_input_registers::register::{register}::count::{count}::values::{registers}')
            # self.logger.debug("READ INPUT: number: {}, Count: {}, values: {}".format(register, count, registers))
            return registers
        else:
            self.logger.debug(f'read_input_registers::simulator') 


    def read_coils(self, register, count):
        if not self.is_simulator():
            bits = self.client.read_coils(register, count=count, unit=self.modbus_id).bits
            self.logger.debug(f'read_coils::register::{register}::count::{count}::values::{bits}')
            # self.logger.info("READ COILS: number: {}, Count: {}, values: {}".format(register, count, bits)) # TODO
            return bits
        else:
            self.logger.debug(f'read_coils::simulator') 


    async def read_registers_in_batch(self, register_start, total_count, max_batch_size=50, register_type=None):
        _start = register_start
        end = register_start + total_count
        registers = []
        while _start < end:
            _count = min(max_batch_size, end - _start)

            if register_type == None or register_type == ModbusRegisterType.HOLDING:
                registers.extend(await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, _start, _count))
            else: # register_type == ModbusRegisterType.INPUT:
                registers.extend(await utils.run_and_try_async(self.read_input_registers, 3, 0.1, _start, _count))

            _start = _start + _count
        return registers


    async def write_value(self, register_num, type_str, value, count=None):
        if not self.is_simulator():
            if type_str in ModbusTypes.__members__:
                value_type = ModbusTypes[type_str]

                if value_type == ModbusTypes.COIL:
                    self.logger.critical(f'write_value::coil::register::{register_num}::value::{value}')
                    # self.logger.critical("WRITING values: {} to coil register number: {}".format(value, register_num))
                    await utils.run_and_try_async(self.client.write_coil, 3, 0.1, register_num, value, unit=self.modbus_id)
                else:

                    builder = BinaryPayloadBuilder(byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)
                    
                    if value_type == ModbusTypes.FLOAT16:
                        builder.add_16bit_float(float(value))
                    elif value_type == ModbusTypes.FLOAT32:
                        builder.add_32bit_float(float(value))
                    elif value_type == ModbusTypes.FLOAT64:
                        builder.add_64bit_float(float(value))

                    elif value_type == ModbusTypes.INT16:
                        builder.add_16bit_int(int(round(float(value))))
                    elif value_type == ModbusTypes.INT32:
                        builder.add_32bit_int(int(round(float(value))))
                    elif value_type == ModbusTypes.INT64:
                        builder.add_64bit_int(int(round(float(value))))

                    elif value_type == ModbusTypes.UINT16:
                        builder.add_16bit_uint(int(round(float(value))))
                    elif value_type == ModbusTypes.UINT32:
                        builder.add_32bit_uint(int(round(float(value))))
                    elif value_type == ModbusTypes.UINT64:
                        builder.add_64bit_uint(int(round(float(value))))

                    elif value_type == ModbusTypes.INT8HIGH:
                        registers = await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, register_num, 1)
                        decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)
                        high_value = decoder.decode_8bit_int() # DISCARD FIRST 8 BIT OF THE 16 BIT MODBUS WORD
                        low_value = decoder.decode_8bit_int()

                        builder.add_8bit_int(int(round(float(value)))) # TODO ROUND INSTEAD OF FLOOR
                        builder.add_8bit_int(low_value)
                    elif value_type == ModbusTypes.INT8LOW:
                        registers = await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, register_num, 1)
                        decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)
                        high_value = decoder.decode_8bit_int() 
                        low_value = decoder.decode_8bit_int()# DISCARD LAST 8 BIT OF THE 16 BIT MODBUS WORD

                        builder.add_8bit_int(high_value)
                        builder.add_8bit_int(int(round(float(value))))

                    elif value_type == ModbusTypes.UINT8HIGH:
                        registers = await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, register_num, 1)
                        decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)
                        high_value = decoder.decode_8bit_uint() # DISCARD FIRST 8 BIT OF THE 16 BIT MODBUS WORD
                        low_value = decoder.decode_8bit_uint()

                        builder.add_8bit_uint(int(round(float(value))))
                        builder.add_8bit_uint(low_value)

                    elif value_type == ModbusTypes.UINT8LOW:
                        registers = await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, register_num, 1)
                        decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)
                        high_value = decoder.decode_8bit_uint() 
                        low_value = decoder.decode_8bit_uint()# DISCARD LAST 8 BIT OF THE 16 BIT MODBUS WORD

                        builder.add_8bit_uint(high_value)
                        builder.add_8bit_uint(int(round(float(value))))

                    elif type_str.startswith('BIT'):
                        registers = await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, register_num, 1)
                        decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)

                        bits_high = decoder.decode_bits()
                        bits_low  = decoder.decode_bits()
                        bit_num   = int(type_str.replace('BIT', '').replace('HIGH', '').replace('LOW', ''))
                        if type_str.endswith("HIGH"):
                            bits_high[bit_num] = value # override single bit of interest
                        elif type_str.endswith("LOW"):
                            bits_low[bit_num] = value # override single bit of interest
                        else: # default low bits
                            bits_low[bit_num] = value # override single bit of interest

                        builder.add_bits(bits_high)
                        builder.add_bits(bits_low)
                    
                    # self.logger.critical('-------------------------------------------------------')
                    self.logger.critical(f'write_value::holding::register::{register_num}::value::{builder.to_registers()}')
                    # self.logger.critical("WRITING values: {} to register number: {}".format(builder.to_registers(), register_num))
                    await utils.run_and_try_async(self.client.write_registers, 3, 0.1, register_num, builder.to_registers(), unit=self.modbus_id)
                    return True
                # self.logger.critical('-------------------------------------------------------')
        else:
            self.logger.info(f'write_value::simulator')
            # print('SIMULATOR: skipping write_value')
            return None

        
    async def read_value(self, register_num, type_str, register_type=None, count=None, array_count=1):
        if array_count is None:
            array_count = 1
        if not self.is_simulator():
            if type_str in ModbusTypes.__members__:
                value_type = ModbusTypes[type_str]
                
                if type_str.startswith('BIT'):
                    count = 1
                elif count == None:
                    if '64' in type_str:
                        count = 4
                    elif '32' in type_str:
                        count = 2
                    elif '16' in type_str:
                        count = 1
                    elif '8' in type_str:
                        count = 1
                    else:
                        count = 1

                if value_type == ModbusTypes.COIL:
                    bits = await utils.run_and_try_async(self.read_coils, 3, 0.1, register_num, count)
                    self.logger.debug(f'read_value::coil::{register_num}::count::{count}::values::{bits}')
                    # self.logger.info('COIL REGISTER_NUM = {}, COUNT: {}, bits: {}'.format(register_num, count, bits))
                    values = bits[:count]
                    return values[0] if count == 1 else values
                else:
                    if register_type == None or register_type == ModbusRegisterType.HOLDING:
                        registers = await utils.run_and_try_async(self.read_holding_registers, 3, 0.1, register_num, count)
                    else: # register_type == ModbusRegisterType.INPUT:
                        registers = await utils.run_and_try_async(self.read_input_registers, 3, 0.1, register_num, count)

                    self.logger.debug(f'read_value::register::{register_num}::count::{count}::values::{registers}')

                    if registers == None:
                        return None

                    decoder = BinaryPayloadDecoder.fromRegisters(registers, byteorder=self.modbus_byteorder, wordorder=self.modbus_wordorder)

                    values = []
                    for _ in range(array_count):
                        if type_str.startswith('BIT'):
                            bits_high = decoder.decode_bits()
                            bits_low  = decoder.decode_bits()
                            bit_num   = int(type_str.replace('BIT', '').replace('HIGH', '').replace('LOW', ''))
                            
                            self.logger.debug(f'read_value::bits_high::{bits_high}::bits_low::{bits_low}::bit_num::{bit_num}')
                            # self.logger.critical(f"bits_high: {bits_high}. bits_low: {bits_low}. bit_num: {bit_num}")
                        
                            if type_str.endswith("HIGH"):
                                value = bits_high[bit_num]
                            elif type_str.endswith("LOW"):
                                value = bits_low[bit_num]
                            else: # default high bits
                                value = bits_high[bit_num]
                            # value = int(registers[0] & (1 << bit_num) == (1 << bit_num)) # TODO TEST IF IT WORKS

                        elif value_type == ModbusTypes.FLOAT16:
                            value = decoder.decode_16bit_float()
                        elif value_type == ModbusTypes.FLOAT32:
                            value = decoder.decode_32bit_float()
                        elif value_type == ModbusTypes.FLOAT64:
                            value = decoder.decode_64bit_float()

                        elif value_type == ModbusTypes.INT16:
                            value = decoder.decode_16bit_int()
                        elif value_type == ModbusTypes.INT32:
                            value = decoder.decode_32bit_int()
                        elif value_type == ModbusTypes.INT64:
                            value = decoder.decode_64bit_int()

                        elif value_type == ModbusTypes.UINT16:
                            value = decoder.decode_16bit_uint()
                        elif value_type == ModbusTypes.UINT32:
                            value = decoder.decode_32bit_uint()
                        elif value_type == ModbusTypes.UINT64:
                            value = decoder.decode_64bit_uint()

                        elif value_type == ModbusTypes.INT8HIGH:
                            value = decoder.decode_8bit_int()
                        elif value_type == ModbusTypes.INT8LOW:
                            decoder.decode_8bit_int() # DISCARD FIRST 8 BIT OF THE 16 BIT MODBUS WORD
                            value = decoder.decode_8bit_int()

                        elif value_type == ModbusTypes.UINT8HIGH:
                            value = decoder.decode_8bit_uint()
                        elif value_type == ModbusTypes.UINT8LOW:
                            decoder.decode_8bit_uint() # DISCARD FIRST 8 BIT OF THE 16 BIT MODBUS WORD
                            value = decoder.decode_8bit_uint()

                        else: 
                            return registers
                            # value = registers
                        values.append(value)
                
                    return values[0] if array_count == 1 else values
            else:
                self.logger.error(f'read_value::invalid_modbus_type::{type_str}')
                # self.logger.error('{} is NOT a valid ModbusTypes value'.format(type_str))
                return None
        else:
            self.logger.info(f'read_value::simulator')
            # self.logger.info('SIMULATOR: skipping read_value')
            return None


    def _get_byteorder(self):
        value = self.get('ENDIAN_BYTEORDER', default='Big') 
        if value.lower() == 'little':
            return Endian.Little
        elif value.lower() == 'auto':
            return Endian.Auto
        else:
            return Endian.Big


    def _get_wordorder(self):
        value = self.get('ENDIAN_WORDORDER', default='Big') 
        if value.lower() == 'little':
            return Endian.Little
        elif value.lower() == 'auto':
            return Endian.Auto
        else:
            return Endian.Big


    async def dump(self, register_start, register_end, max_count, register_type):
        return await self.read_registers_in_batch(register_start, register_end - register_start, max_batch_size=max_count, register_type=register_type)