from abc import ABC, abstractmethod
import logging
import math
import traceback

import library.utils as utils
from library.base_db_manager import BaseDBManager, Query


class Measurement(ABC):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        self.sensor_type = sensor_type
        self.machine_type = machine_type
        self.command = utils.get(properties_dict, 'COMMAND', default=None)

        self.interval = utils.parse_float(utils.get(properties_dict, 'INTERVAL', default=3600., common_dictionary=common_dictionary), default=3600.)
        self.uom = utils.get(properties_dict, 'UOM', default=None, common_dictionary=common_dictionary)
        self.skip_same_value = utils.parse_bool(utils.get(properties_dict, 'SKIP_SAME_VALUE', default=None, common_dictionary=common_dictionary), default=True)
        self.skip_max_time = utils.parse_float(utils.get(properties_dict, 'SKIP_MAX_TIME', default=None, common_dictionary=common_dictionary), default=900.)
        self.skip_threshold = utils.parse_float(utils.get(properties_dict, 'SKIP_THRESHOLD', default=None, common_dictionary=common_dictionary), default=1.e-6)
        self.skip_first = utils.parse_bool(utils.get(properties_dict, 'SKIP_FIRST', default=False, common_dictionary=common_dictionary), default=False)
        self.scale = utils.parse_float(utils.get(properties_dict, 'SCALE', default=1., common_dictionary=common_dictionary), default=1.)
        self.offset = utils.parse_float(utils.get(properties_dict, 'OFFSET', default=0., common_dictionary=common_dictionary), default=0.)
        self.not_send = utils.parse_bool(utils.get(properties_dict, 'NOT_SEND', default=False, common_dictionary=common_dictionary), default=False)
        self.operation = utils.get(properties_dict, 'OPERATION', default='READ', common_dictionary=common_dictionary)
        self.write_value = utils.parse_float(utils.get(properties_dict, 'VALUE', default=None, common_dictionary=common_dictionary), default=None)
        self.version = utils.parse_int(utils.get(properties_dict, 'VERSION', default=None, common_dictionary=common_dictionary), default=None)
        self.module_type = utils.get(properties_dict, 'MODULE_TYPE', default=None, common_dictionary=common_dictionary)
        self.pre_write_command = utils.get(properties_dict, 'PRE_WRITE_COMMAND', default=None, common_dictionary=common_dictionary)  # SENSOR_TYPE OF PRE WRITE COMMAND
        self.post_write_command = utils.get(properties_dict, 'POST_WRITE_COMMAND', default=None, common_dictionary=common_dictionary)  # SENSOR_TYPE OF POST WRITE COMMAND
        self.enabled = utils.parse_bool(utils.get(properties_dict, 'ENABLED', default=None, common_dictionary=common_dictionary), default=True)
        self.target_bit = utils.parse_int(utils.get(properties_dict, 'TARGET_BIT', default=None, common_dictionary=common_dictionary), default=None)
        self.target_bitmask_name = utils.get(properties_dict, 'TARGET_BITMASK_NAME', default=None, common_dictionary=common_dictionary)
        self.output_list = utils.get_single_or_list(properties_dict, 'OUTPUT', default=['output1'], common_dictionary=common_dictionary)

        self.already_skipped = False  # flag to be toggled in case of skip first

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
        logging.getLogger().info(f'newvalue: {new_value}. value: {self.value}. skip_threshold: {self.skip_threshold}')  ###############################################################
        logging.getLogger().info(f'new_time: {new_time}. time: {self.time}. skip_max_time: {self.skip_max_time}')  ###############################################################
        print(f'newvalue: {new_value}. value: {self.value}. skip_threshold: {self.skip_threshold}')  ###############################################################
        print(f'new_time: {new_time}. time: {self.time}. skip_max_time: {self.skip_max_time}')  ###############################################################

        if not self.skip_same_value:
            self.set_value(new_time, new_value, uom=uom)
            return True

        value_threshold_flag = self.value is not None and abs(new_value - self.value) > self.skip_threshold
        time_threshold_flag = self.time is not None and (new_time - self.time).total_seconds() > self.skip_max_time

        if (
                self.value is None or
                self.time is None or
                value_threshold_flag or
                time_threshold_flag
        ):
            self.old_value = self.value
            self.old_time = self.time
            self.set_value(new_time, new_value, uom=uom)
            if not value_threshold_flag:  # not keep track of latest if we are updating due to long time from latest
                self.latest_time = None
                self.latest_value = None
            logging.getLogger().info(f'can_send: TRUE. new_value: {new_value}. self.value: {self.value}. new_time {new_time}. self.time: {self.time}')  ###############################################################
            return True
        else:
            self.latest_time = new_time
            self.latest_value = new_value
            logging.getLogger().info(f'can_send: FALSE')  ###############################################################
            return False

    def _get_type_key_(self):
        return 'sensor_type'

    def _get_default_version_(self):
        return 0

    def _get_default_module_type_(self):
        return None

    def get_messages_json(self, current_only=False):
        if self.not_send:
            return []

        payloads = []
        # if we do not skip same value,we have already sent the latest
        if (
                self.skip_same_value and
                not current_only and
                self.latest_value is not None and
                self.latest_time is not None and
                (isinstance(self.latest_value, list) or not math.isnan(self.latest_value))
        ):
            if self.time != self.latest_time and self.value != self.latest_value:
                # append latest value before the jump
                if not math.isnan(self.latest_value):
                    logging.getLogger().critical(f"SENDING EVEN THE LATEST VALUE!! {vars(self)}")

                    msg = {}
                    msg[self._get_type_key_()] = self.sensor_type
                    msg['time'] = self.latest_time.strftime('%Y-%m-%dT%H:%M:%S')  # .isoformat()
                    msg['machine_type'] = self.machine_type
                    msg['value'] = self.post_process_value(self.latest_value)
                    msg['uom'] = self.uom
                    msg['version'] = self.version if self.version is not None else self._get_default_version_()
                    msg['module_type'] = self.module_type if self.module_type is not None else self._get_default_module_type_()
                    # TODO
                    # if msg['version'] is None: # in case of None version we let the azure function to guess a default value
                    #     def msg['version'] 

                    payloads.append(msg)
                    # payloads.append({'time': self.latest_time.isoformat(), 'machine_type': self.machine_type, self._get_type_key_(): self.sensor_type, 'value': self.post_process_value(self.latest_value), 'uom': self.uom})
                self.latest_time = None
                self.latest_value = None

        if self.value is not None and (isinstance(self.value, list) or not math.isnan(self.value)):
            msg = {}
            msg[self._get_type_key_()] = self.sensor_type
            msg['time'] = self.time.strftime('%Y-%m-%dT%H:%M:%S')  # .isoformat()
            msg['machine_type'] = self.machine_type
            msg['value'] = self.post_process_value(self.value)
            msg['uom'] = self.uom
            msg['version'] = self.version if self.version is not None else self._get_default_version_()
            msg['module_type'] = self.module_type if self.module_type is not None else self._get_default_module_type_()
            # TODO
            # if msg['version'] is None: # in case of None version we let the azure function to guess a default value
            #     def msg['version'] 

            payloads.append(msg)
            # payloads.append({'time': self.time.isoformat(), 'machine_type': self.machine_type, self._get_type_key_(): self.sensor_type, 'value': self.post_process_value(self.value), 'uom': self.uom})

        logging.getLogger().info(f'get_messages_json: {payloads}')  ###############################################################
        return payloads


class ModbusMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

        self.register_number = utils.parse_int(utils.get(properties_dict, 'REGISTER_NUMBER', default=3600., common_dictionary=common_dictionary), default=None)
        self.index = utils.parse_int(utils.get(properties_dict, 'INDEX', default=1, common_dictionary=common_dictionary), default=None)
        self.register_type = utils.get(properties_dict, 'REGISTER_TYPE', default=None, common_dictionary=common_dictionary)
        self.value_type = utils.get(properties_dict, 'VALUE_TYPE', default=None, common_dictionary=common_dictionary)
        self.count = utils.get(properties_dict, 'COUNT', default=None, common_dictionary=common_dictionary)
        self.array_count = utils.get(properties_dict, 'ARRAY_COUNT', default=1, common_dictionary=common_dictionary)


class FunctionMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)
        self.function = utils.get(properties_dict, 'FUNCTION', default=None, common_dictionary=common_dictionary)

    def evaluate(self, measurement_list):
        import library.math_parser as math_parser
        measurement_dict = {m.sensor_type: m for m in measurement_list}
        parser = math_parser.NumericStringParser(measurement_dict)

        try:
            value = parser.eval(self.function)
            return value
        except Exception as e:
            logging.error('ERROR in evaluate parser {}. traceback: {}'.format(e, traceback.format_exc()))
            logging.debug(e, exc_info=True)
            return None

class FunctionCheckModbus(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

        self.variable_2_check           = utils.get(properties_dict, 'VARIABLE_2_CHECK', default=None, common_dictionary=common_dictionary)
        self.uom_2_check                = utils.get(properties_dict, 'UOM_2_CHECK', default=None, common_dictionary=common_dictionary)
        self.upper_bound                = utils.parse_float(utils.get(properties_dict, 'UPPER_BOUND', default=None, common_dictionary=common_dictionary), default=1000)
        self.lower_bound                = utils.parse_float(utils.get(properties_dict, 'LOWER_BOUND', default=None, common_dictionary=common_dictionary), default=0)
        self.upper_bound_variable       = utils.get(properties_dict, 'UPPER_BOUND_VARIABLE', default=None, common_dictionary=common_dictionary)
        self.upper_value_default        = utils.parse_float(utils.get(properties_dict, 'UPPER_VALUE_DEFAULT', default=None, common_dictionary=common_dictionary), default=1000)
        self.lower_bound_variable       = utils.get(properties_dict, 'LOWER_BOUND_VARIABLE', default=None, common_dictionary=common_dictionary)
        self.lower_value_default        = utils.parse_float(utils.get(properties_dict, 'LOWER_VALUE_DEFAULT', default=None, common_dictionary=common_dictionary), default=0)
        self.between_bounds_variable    = utils.get(properties_dict, 'BETWEEN_BOUNDS_VARIABLE', default=None, common_dictionary=common_dictionary)
        self.between_value_default      = utils.parse_float(utils.get(properties_dict, 'BETWEEN_VALUE_DEFAULT', default=None, common_dictionary=common_dictionary), default=0)
        self.default_value              = utils.parse_float(utils.get(properties_dict, 'DEFAULT_VALUE', default=None, common_dictionary=common_dictionary), default=0)
        self.output_variable_name       = utils.get(properties_dict, 'OUTPUT_VARIABLE', default=None, common_dictionary=common_dictionary)
        self.output_variable = None

    def evaluate(self, measurement_list):
        measurement_dict = {m.sensor_type: m for m in measurement_list}

        try:
            variable_2_check    = utils.get(measurement_dict, self.variable_2_check)
            self.output_variable     = utils.get(measurement_dict, self.output_variable_name)
            if variable_2_check is not None and self.output_variable is not None:
                upper_bound_val     = utils.get(measurement_dict, self.upper_bound_variable).value if self.upper_bound_variable is not None else self.upper_value_default
                lower_bound_val     = utils.get(measurement_dict, self.lower_bound_variable).value if self.lower_bound_variable is not None else self.lower_value_default
                between_bounds_val  = utils.get(measurement_dict, self.between_bounds_variable).value if self.between_bounds_variable is not None else self.between_value_default
                # upper bound
                if variable_2_check.value > self.upper_bound: 
                    value = upper_bound_val
                    logging.debug(f'function_check::variable:{self.variable_2_check}:{variable_2_check.value}  > upper_bound:{self.upper_bound:}')
                elif variable_2_check.value < self.lower_bound:
                    value = lower_bound_val
                    logging.debug(f'function_check::variable:{self.variable_2_check}:{variable_2_check.value}  < lower_bound:{self.lower_bound:}')
                else:
                    value = between_bounds_val
                    logging.debug(f'function_check::variable:{self.variable_2_check}:{variable_2_check.value}  > lower_bound:{self.lower_bound:} and < upper_bound:{self.upper_bound}' )
                # output variable
                self.output_variable.write_value = value
            else:
                value=self.default_value
            return value
        except Exception as e:
            logging.error('ERROR in evaluate parser {}. traceback: {}'.format(e, traceback.format_exc()))
            logging.debug(e, exc_info=True)
            return None


class QueryMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)
        self.query = properties_dict['QUERY']  # Mandatory

    def evaluate(self, db_manager):
        if self.query is None or len(self.query) == 0:
            return None

        result = db_manager.query_execute(Query(self.query), fetch=True, aslist=True)
        # result examples:
        # - [24.2599998]
        # - [None]
        result = result[0]

        return result


class BitmaskMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def evaluate(self, measurement_list):
        value = 0
        for measurement in measurement_list:
            if measurement.target_bitmask_name is not None and measurement.target_bit is not None:
                if measurement.target_bitmask_name == self.sensor_type:
                    if isinstance(measurement.value, list):
                        for i, v in enumerate(value):
                            # first item in the list goes to lowest bit
                            value = value + (bool(round(v)) << measurement.target_bit + i)
                    elif math.fabs(value, round(value)) < 1e-10:  # manage it as an int of many bits
                        value = value + (int(round(measurement.value)) << measurement.target_bit)
                    else:  # cast as bool
                        value = value + (bool(round(measurement.value)) << measurement.target_bit)
        return value


class AdamMeasurement(Measurement):

    def __init__(self, machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, sensor_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

        self.channel = utils.parse_int(utils.get(properties_dict, 'CHANNEL', default=0, common_dictionary=common_dictionary), default=None)
        self.min_range = utils.parse_float(utils.get(properties_dict, 'MIN_RANGE', default=None, common_dictionary=common_dictionary), default=None)
        self.max_range = utils.parse_float(utils.get(properties_dict, 'MAX_rANGE', default=None, common_dictionary=common_dictionary), default=None)


class ConfigMeasurement(Measurement):

    def __init__(self, machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def _get_type_key_(self):
        return 'configuration_type'

    def _get_default_version_(self):
        return 1000


class ConfigModbusMeasurement(ModbusMeasurement):

    def __init__(self, machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def _get_type_key_(self):
        return 'configuration_type'

    def _get_default_version_(self):
        return 1000


class ConfigFunctionMeasurement(FunctionMeasurement):

    def __init__(self, machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def _get_type_key_(self):
        return 'configuration_type'

    def _get_default_version_(self):
        return 1000

class ConfigFunctionCheckModbus(FunctionCheckModbus):

    def __init__(self, machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def _get_type_key_(self):
        return 'configuration_type'

    def _get_default_version_(self):
        return 1000


class ConfigQueryMeasurement(QueryMeasurement):

    def __init__(self, machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def _get_type_key_(self):
        return 'configuration_type'

    def _get_default_version_(self):
        return 1000


class ConfigBitmaskMeasurement(BitmaskMeasurement):

    def __init__(self, machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=None):
        super().__init__(machine_type, configuration_type, properties_dict, common_dictionary, parameters_keys=parameters_keys)

    def _get_type_key_(self):
        return 'configuration_type'

    def _get_default_version_(self):
        return 1000


if __name__ == "__main__":
    import datetime
    import time

    delta_time = 0.1
    max_delta_time = 11 * 0.1

    a = {"SKIP_SAME_VALUE": True, "SKIP_MAX_TIME": max_delta_time, 'SKIP_THRESHOLD': 1e-15}

    m = Measurement("MACHINE_TYPE", 'SENSOR_TYPE', a, {})

    values_1 = [0] * 20 + [1] * 1 + [0] * 20

    results = []

    for value in values_1:
        m.can_send(datetime.datetime.utcnow(), value)
        results.extend(m.get_messages_json())
        time.sleep(delta_time)