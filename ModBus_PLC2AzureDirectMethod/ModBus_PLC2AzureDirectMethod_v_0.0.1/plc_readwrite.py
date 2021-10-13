import library.utils as utils
from enum import Enum, auto
from library.plc_modbus import PlcModbus
from datetime import datetime
from library.measurement import Measurement

class PlcVariableTags(Enum):
    REGISTER_NUMBER = auto()
    VALUE_TYPE = auto()
    VALUE = auto()
    WRITE_VALUE = auto()
    TIME = auto()
    R_SAMPLING_TIME_MS = auto()
    MEASUREMENTS = auto()
    MEASUREMENT_NAMES = auto()
    OFFSET = auto()
    SCALE = auto()

class PlcRwMode(Enum):
    READ = auto()
    WRITE = auto()


class PlcReadWrite():
    def __init__(self, logger, plc_config_dict):
        self.logger = logger
        self.name                   =   utils.get(plc_config_dict,'NAME', "plc_test")
        self.priority               =   utils.get(plc_config_dict,'PRIORITY', 1)
        self.rw_mode                =   PlcRwMode[utils.get(plc_config_dict,'RW_MODE', 'READ')]
        self.max_attempts           =   utils.get(plc_config_dict,'MAX_ATTEMPTS', 3)
        setup                       =   utils.get(plc_config_dict,'SETUP')
        self.measurement_list_dict  =   utils.get(setup,'MODBUS_MEASUREMENTS')
        for group in self.measurement_list_dict:
            group[PlcVariableTags.MEASUREMENT_NAMES.name] = [list(value.keys())[0] for value in group[PlcVariableTags.MEASUREMENTS.name]]
        self.device_instance        =   PlcModbus(self.logger, variables_dict=setup)

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
            register_number=utils.get(vals, PlcVariableTags.REGISTER_NUMBER.name)
            value_type=utils.get(vals, PlcVariableTags.VALUE_TYPE.name)
            scale = utils.get(vals, PlcVariableTags.SCALE.name, 1)
            offset = utils.get(vals, PlcVariableTags.OFFSET.name, 0)
            result = await self.device_instance.read_value(register_number, value_type, register_type=None, count=None, array_count=1)
            self.logger.debug(f'reading::{key}::{register_number}::value type::{value_type}::value::{result}')
            #aggiunta del valore
            vals[PlcVariableTags.VALUE.name]=result
            vals[PlcVariableTags.WRITE_VALUE.name]=self.post_process_value(result, scale, offset)
            vals[PlcVariableTags.TIME.name]= datetime.utcnow().isoformat()
        except Exception as e:
            self.logger.critical(f'error::{e}')
        return result

    async def write_var_async(self, meas_dict, value):
        result = None
        try:
            # acquisizione della chiave
            key=list(meas_dict.keys())[0]
            # acquisizione dei parametri
            vals=list(meas_dict.values())[0]
            # scrittura della variabile
            register_number=utils.get(vals, PlcVariableTags.REGISTER_NUMBER.name)
            value_type=utils.get(vals, PlcVariableTags.VALUE_TYPE.name)
            result = await self.device_instance.write_value(register_number, value_type, value)
            self.logger.debug(f'write::{key}::{register_number}::value type::{value_type}::values::{value}')
        except Exception as e:
            self.logger.critical(f'error::{e}')
        return result


    def post_process_value(self, value, scale, offset):
        return value * scale + offset