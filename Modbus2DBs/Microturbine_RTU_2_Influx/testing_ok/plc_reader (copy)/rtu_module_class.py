import datetime
from library.rtu_modbus import RtuModbus, ModbusRegisterType
import library.utils as utils
from enum import Enum, auto
from datetime import datetime

class ModbusVariableTags(Enum):
    REGISTER_NUMBER = auto()
    VALUE_TYPE = auto()
    VALUE = auto()
    TIME = auto()
    R_SAMPLING_TIME_MS = auto()
    MEASUREMENTS = auto()
    REGISTER_TYPE = auto()


class RtuModuleClass():

    MACHINE_TYPE = "RTU"
    async_cmd_list=[]

    def __init__(self, logger, modbus_config_dict):
        self.modbus_port = utils.get(modbus_config_dict,'MODBUS_PORT', '/dev/ttyUSB0')
        self.modbus_stopbits = utils.get(modbus_config_dict,'MODBUS_STOPBITS',  1)
        self.modbus_bytesize = utils.get(modbus_config_dict,'MODBUS_BYTESIZE', 8)
        self.modbus_baudrate = utils.get(modbus_config_dict,'MODBUS_BAUDRATE', 9600)
        self.modbus_timeout = utils.get(modbus_config_dict,'MODBUS_TIMEOUT', 1)
        self.modbus_method = utils.get(modbus_config_dict,'MODBUS_METHOD', 'rtu')
        self.modbus_parity = utils.get(modbus_config_dict,'MODBUS_PARITY', 'E')
        self.max_attempts=utils.get(modbus_config_dict,'MAX_ATTEMPTS', 3)
        self.measurement_list_dict = utils.get(modbus_config_dict,'MODBUS_MEASUREMENTS')
        self.logger = logger
        self.device_instance = RtuModbus(self.logger, self.modbus_port, self.modbus_stopbits, 
                self.modbus_bytesize, self.modbus_baudrate,
                self.modbus_timeout, self.modbus_method, self.modbus_parity,
                variables_dict=modbus_config_dict)


    def get_meas_info_from_name(self, meas_name)->dict:
        for m in self.measurement_list_dict:
            if list(m.keys())[0] == meas_name:
                return list(m.values())[0]
        return None

#############################################################################################
### INIZIALIZZAZIONE e Shut down

    def connect_device(self):
        return self.device_instance.connect()        

    def disconnect_device(self):
        return self.device_instance.disconnect()

#############################################################################################
### LETTURA variabili

    async def read_var_async(self, meas_dict):
        result = None
        try:
            # acquisizione della chiave
            key=list(meas_dict.keys())[0]
            # acquisizione dei parametri
            vals=list(meas_dict.values())[0]
            register_number=utils.get(vals, ModbusVariableTags.REGISTER_NUMBER.name)
            register_type_name = utils.get(vals, ModbusVariableTags.REGISTER_TYPE.name)
            register_type = ModbusRegisterType[register_type_name] if register_type_name in [r.name for r in ModbusRegisterType] else None
            value_type= utils.get(vals, ModbusVariableTags.VALUE_TYPE.name)
            
            self.logger.debug(f'reading::{key}::{register_number}::value type::{value_type}')
            result = await self.device_instance.read_value(register_number, value_type, register_type=register_type, count=None, array_count=1)
            #aggiunta del valore
            vals[ModbusVariableTags.VALUE.name]=result
            vals[ModbusVariableTags.TIME.name]=datetime.utcnow().isoformat()
        except Exception as e:
            self.logger.critical(f'error::{e}')
        return result

