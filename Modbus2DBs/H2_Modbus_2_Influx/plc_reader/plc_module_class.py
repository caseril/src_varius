import datetime
from library.plc_modbus import PlcModbus
import library.utils as utils
from enum import Enum, auto
from datetime import datetime

class PlcVariableTags(Enum):
    REGISTER_NUMBER = auto()
    VALUE_TYPE = auto()
    VALUE = auto()
    TIME = auto()
    R_SAMPLING_TIME_MS = auto()
    MEASUREMENTS = auto()


class PlcModuleClass():

    MACHINE_TYPE = "INGRID"
    async_cmd_list=[]

    def __init__(self, logger, plc_config_dict):
        self.ip = utils.get(plc_config_dict,'MODBUS_IP', "192.168.0.1")
        self.port = utils.get(plc_config_dict,'MODBUS_PORT', 502)
        self.max_attempts=utils.get(plc_config_dict,'MAX_ATTEMPTS', 3)
        self.measurement_list_dict = utils.get(plc_config_dict,'MODBUS_MEASUREMENTS')
        self.logger = logger
        self.device_instance = PlcModbus(self.logger, variables_dict=plc_config_dict, ip=self.ip, port = self.port)


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
            
            self.logger.debug(f'reading::{key}::{register_number}::value type::{value_type}')
            result = await self.device_instance.read_value(register_number, value_type, register_type=None, count=None, array_count=1)
            #aggiunta del valore
            vals[PlcVariableTags.VALUE.name]=result
            vals[PlcVariableTags.TIME.name]=datetime.utcnow().isoformat()
        except Exception as e:
            self.logger.critical(f'error::{e}')
        return result

