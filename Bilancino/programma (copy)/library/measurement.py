from abc import ABC, abstractmethod
import logging
import sys
import math
import traceback


import library.utils as utils


# logging.basicConfig(filename='log.measurement', filemode='w', format='%(asctime)s - %(module)s - %(name)s - %(levelname)s - %(message)s')
# logging.getLogger(__name__).setLevel(logging.DEBUG)
# logging.getLogger("pymodbus").setLevel(logging.CRITICAL)
# logging.getLogger("azure.iot").setLevel(logging.CRITICAL)
# logging.getLogger("azure").setLevel(logging.CRITICAL)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

class Measurement(ABC):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        self.sensor_type =  sensor_type
        self.machine_type = machine_type
        self.command = utils.get(properties_dict, 'COMMAND', default=None)
    
        self.interval               = utils.parse_float( utils.get(properties_dict, 'INTERVAL',              default=3600., common_dictionary=common_dictionary), default=3600.)
        self.uom                    =                    utils.get(properties_dict, 'UOM',                   default=None, common_dictionary=common_dictionary)
        self.skip_same_value        = utils.parse_bool(  utils.get(properties_dict, 'SKIP_SAME_VALUE',       default=None, common_dictionary=common_dictionary), default=True)
        self.skip_max_time          = utils.parse_float( utils.get(properties_dict, 'SKIP_MAX_TIME',         default=None, common_dictionary=common_dictionary), default=900.)
        self.skip_threshold         = utils.parse_float( utils.get(properties_dict, 'SKIP_THRESHOLD',        default=None, common_dictionary=common_dictionary), default=1.e-6)
        self.skip_first             = utils.parse_bool(  utils.get(properties_dict, 'SKIP_FIRST',            default=False, common_dictionary=common_dictionary), default=False)
        self.scale                  = utils.parse_float( utils.get(properties_dict, 'SCALE',                 default=1., common_dictionary=common_dictionary), default=1.)
        self.offset                 = utils.parse_float( utils.get(properties_dict, 'OFFSET',                default=0., common_dictionary=common_dictionary), default=0.)
        self.not_send               = utils.parse_bool(  utils.get(properties_dict, 'NOT_SEND',              default=False, common_dictionary=common_dictionary), default=False)
        self.operation              =                    utils.get(properties_dict, 'OPERATION',             default='READ', common_dictionary=common_dictionary)
        self.value                  = utils.parse_float( utils.get(properties_dict, 'VALUE',                 default=None,   common_dictionary=common_dictionary), default=None)
        self.already_skipped        = False # flag to be toggled in case of skip first


        self.time = None
        self.value = None

        # time and value not sent
        self.latest_time = None
        self.latest_value = None

        # old time and value sent
        self.old_time = None
        self.old_value = None

        self.parameters = {}
        if parameters_keys is not None:
            for key in parameters_keys:
                self.parameters[key] = utils.get(properties_dict, key, default=None, common_dictionary=common_dictionary)
    

    def set_value(self, time, value, uom=None):
        # self.latest_time = None
        # self.latest_value = None
        # self.latest_time = self.time
        # self.latest_value = self.value
        self.time = time
        self.value = value
        if uom is not None:
            self.uom = uom 


    @property
    def value_processed(self):
        return self.post_process_value(self.value)


    @property
    def old_value_processed(self):
        return self.post_process_value(self.old_value)


    @property
    def latest_value_processed(self):
        return self.post_process_value(self.old_value)


    def post_process_value(self, value):
        if isinstance(value, list):
            return [v * self.scale + self.offset for v in value]
        else:
            return value * self.scale + self.offset


    def can_send(self, new_time, new_value, uom=None):
        # UPDATE THE VALUE AND RETURN IF CAN SEND
        logging.getLogger().info(f'newvalue: {new_value}. value: {self.value}. skip_threshold: {self.skip_threshold}') ###############################################################
        logging.getLogger().info(f'new_time: {new_time}. time: {self.time}. skip_max_time: {self.skip_max_time}') ###############################################################
        print(f'newvalue: {new_value}. value: {self.value}. skip_threshold: {self.skip_threshold}') ###############################################################
        print(f'new_time: {new_time}. time: {self.time}. skip_max_time: {self.skip_max_time}') ###############################################################

        if not self.skip_same_value:
            self.set_value(new_time, new_value, uom=uom)
            return True

        value_threshold_flag = self.value   is not None     and     abs(new_value - self.value) > self.skip_threshold 
        time_threshold_flag  = self.time    is not None     and     (new_time - self.time).total_seconds() > self.skip_max_time

        if (
                self.value      is   None     or 
                self.time       is   None     or 
                value_threshold_flag          or 
                time_threshold_flag
            ):
            self.old_value = self.value
            self.old_time = self.time
            self.set_value(new_time, new_value, uom=uom)
            if not value_threshold_flag: # not keep track of latest if we are updating due to long time from latest
                self.latest_time = None
                self.latest_value = None
            # self.latest_time = None
            # self.latest_value = None
            # self.time = new_time
            # self.value = new_value
            # if uom is not None:
            #     self.uom = uom
            logging.getLogger().info(f'can_send: TRUE. new_value: {new_value}. self.value: {self.value}. new_time {new_time}. self.time: {self.time}') ###############################################################
            return True
        else:
            self.latest_time = new_time
            self.latest_value = new_value

            # print("self.latest_value is not None", self.latest_value is not None)
            # print("self.latest_time  is not None", self.latest_time  is not None)
            logging.getLogger().info(f'can_send: FALSE') ###############################################################
            return False


    def get_messages_json(self, current_only=False):
        if self.not_send: 
            return []

        payloads = []
        # if we do not skip same value,we have already sent the latest
        if (
                self.skip_same_value                    and   
                not current_only                        and 
                self.latest_value is not None           and
                self.latest_time is not None            and
                ( isinstance(self.latest_value, list) or not math.isnan(self.latest_value) )
            ):
            if self.time != self.latest_time and self.value != self.latest_value:
                # append latest value before the jump
                if not math.isnan(self.latest_value):
                    logging.getLogger().critical(f"SENDING EVEN THE LATEST VALUE!! {vars(self)}")
                    payloads.append({'time': self.latest_time.isoformat(), 'machine_type': self.machine_type, 'sensor_type': self.sensor_type, 'value': self.post_process_value(self.latest_value), 'uom': self.uom})
                self.latest_time = None
                self.latest_value = None

        if self.value is not None and ( isinstance(self.value, list) or not math.isnan(self.value) ):
            payloads.append({'time': self.time.isoformat(), 'machine_type': self.machine_type, 'sensor_type': self.sensor_type, 'value': self.post_process_value(self.value), 'uom': self.uom})

        logging.getLogger().info(f'get_messages_json: {payloads}') ###############################################################
        return payloads


class ModbusMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)
    
        self.register_number        = utils.parse_int(      utils.get(properties_dict, 'REGISTER_NUMBER',       default=3600.,  common_dictionary=common_dictionary), default=None)
        self.register_type          =                       utils.get(properties_dict, 'REGISTER_TYPE',         default=None,   common_dictionary=common_dictionary)
        self.value_type             =                       utils.get(properties_dict, 'VALUE_TYPE',            default=None,   common_dictionary=common_dictionary)
        self.count                  =                       utils.get(properties_dict, 'COUNT',                 default=None,   common_dictionary=common_dictionary)
        self.array_count            =                       utils.get(properties_dict, 'ARRAY_COUNT',           default=1,      common_dictionary=common_dictionary)


class FunctionMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)
        self.function               =                       utils.get(properties_dict, 'FUNCTION',         default=None, common_dictionary=common_dictionary)


    def evaluate(self, measurement_list):
        import library.math_parser as math_parser
        measurement_dict = { m.sensor_type: m for m in measurement_list}

        # logging.getLogger().critical('=============================================')
        # for key in measurement_dict:
        #     logging.getLogger().critical(f'{key}: {vars(measurement_dict[key])}')
        # logging.getLogger().critical('=============================================')

        parser = math_parser.NumericStringParser(measurement_dict)

        try:
            value = parser.eval(self.function)
            return value
        except Exception as e: 
            logging.error('ERROR in evaluate parser {}. traceback: {}'.format(e, traceback.format_exc()))
            logging.debug(e, exc_info=True) 
            return None


class AdamMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)
    
        self.channel        = utils.parse_int(     utils.get(properties_dict, 'CHANNEL',       default=0, common_dictionary=common_dictionary), default=None)
        self.min_range      = utils.parse_float(   utils.get(properties_dict, 'MIN_RANGE',     default=None, common_dictionary=common_dictionary), default=None)
        self.max_range      = utils.parse_float(   utils.get(properties_dict, 'MAX_rANGE',     default=None, common_dictionary=common_dictionary), default=None)
        

if __name__ == "__main__":
    
    import datetime
    import time

    delta_time = 0.1
    max_delta_time = 11*0.1

    a = {"SKIP_SAME_VALUE": True, "SKIP_MAX_TIME": max_delta_time, 'SKIP_THRESHOLD': 1e-15}

    m = Measurement("MACHINE_TYPE", 'SENSOR_TYPE', a, {}) 

    values_1 = [0] * 20 + [1] * 1 + [0] * 20 

    results = []

    for value in values_1:
        m.can_send(datetime.datetime.utcnow(), value)
        results.extend(m.get_messages_json())
        time.sleep(delta_time)