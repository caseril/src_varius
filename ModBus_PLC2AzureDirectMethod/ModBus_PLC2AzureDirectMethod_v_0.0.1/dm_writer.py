import library.utils as utils
import library.remote_methods_caller as rmc


class DM_Wrter():
    def __init__(self, logger, configs_dict):
        self.logger = logger
        self.retry_count           =   utils.get(configs_dict,'RETRY_COUNT', 3)
        self.name                  =   utils.get(configs_dict,'NAME', "plc_test")
        self.priority              =   utils.get(configs_dict,'PRIORITY', 1)
        self.measurement_list_dict  =   utils.get(configs_dict,'MEASUREMENTS')
        self.measurement_names = [list(value.keys())[0] for value in self.measurement_list_dict]



    def get_meas_info_from_name(self, meas_name)->dict:
        for m in self.measurement_list_dict:
            if list(m.keys())[0] == meas_name:
                return list(m.values())[0]
        return None


    async def write_var_async(self, meas_dict, value):
        result = None
        try:
            # acquisizione della chiave
            key=list(meas_dict.keys())[0]
            # acquisizione dei parametri
            vals=list(meas_dict.values())[0]
            # scrittura della variabile
            deviceID=utils.get(vals, 'DEVICE_ID')
            moduleID=utils.get(vals, 'MODULE_ID')
            methodName=utils.get(vals, 'METHOD_NAME')
            payload={key:{"VALUE": value}}
            done, message, code = rmc.call_direct_method(deviceID, moduleID, methodName, payload)
            self.logger.debug(f'write::{key}::deviceId{deviceID}::moduleId::{moduleID}::methodName::{methodName}::payload::{payload}')
            self.logger.debug(f'done::{done}::message::{message}::code{code}')
        except Exception as e:
            self.logger.critical(f'error::{e}')
        return result