import time
import os
import sys
import asyncio
from six.moves import input
from datetime import datetime, timedelta
import json
import threading
import logging
import traceback
import hashlib
import subprocess
import csv
import re


#######################################################################

def parse_json(payload):
    try:
        return json.loads(payload)
    except:
        return None


def parse_int(string, default=0):
    try:
        return int(string)
    except:
        return default


def parse_float(string, default=0.):
    try:
        return float(string)
    except:
        return default


def parse_bool(string, default=False):
    if string is None:
        return default
    try:
        return str(string).lower() in ['true', 't', 'on', '1']
    except:
        return default


def parse_list(obj, default=[]):
    if obj is None:
        return default
    try:    
        if isinstance(obj, list):
            return obj
        if ',' in obj:
            return obj.split(',')
        else:
            return obj.split()
    except:
        return default


def parse_reading_env(string, fields=[]):
    try:
        dictionary = json.loads(string)
        key = list(dictionary.keys())[0]
        if all(field in dictionary[key] for field in fields):
        # if "register" in dictionary[key] and "type" in dictionary[key] and "uom" in dictionary[key]: 
            # return dictionary["register"], dictionary["type"], dictionary["uom"]
            # print(string, dictionary)
            return key, dictionary[key]
        return None, None
    except:
        return None, None


def parse_reading_envs_dict(fields=[]):
    dictionary = {}
    for env in os.environ:
        if env.startswith('READING_VALUES_'):
            key, value = parse_reading_env(os.getenv(env), fields=fields)
            dictionary[key] = value
    return dictionary # [parse_reading_env(os.getenv(env)) for env in os.environ if env.startswith('READING_VALUES_')]

#############################################################

def get_measurement_list_from_dict(machine_type, dictionary, parameters_keys=None, logger=None):
    logger = logging.getLogger() if logger is None else logger

    import library.measurement
    measurement_list = []
    prefix_classes_dict = {}
    prefix_classes_dict['MEASUREMENT_']            =   library.measurement.Measurement
    # prefix_classes_dict['ADAM_MEASUREMENT_']       =   library.measurement.AdamMeasurement
    prefix_classes_dict['MODBUS_MEASUREMENT_']     =   library.measurement.ModbusMeasurement
    prefix_classes_dict['QUERY_MEASUREMENT_']      =   library.measurement.QueryMeasurement
    prefix_classes_dict['FUNCTION_MEASUREMENT_']   =   library.measurement.FunctionMeasurement
    for key in sorted(dictionary): # sorted(dictionary) returns a list of keys sorted alphabetically
        for p in prefix_classes_dict:
            if key.startswith(p):
                try:
                    # dictionary[key] is a dictionary in string
                    measurement_dict = json.loads(dictionary[key])
                    sensor_type = list(measurement_dict.keys())[0]
                    measurement = prefix_classes_dict[p](machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
                    measurement_list.append(measurement)
                except Exception as e:
                    logger.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
                    logger.debug(e, exc_info=True) 

    return measurement_list


#############################################################
# RETROCOMPATIBILITÀ 
#############################################################
def get_all_measurement_list(machine_type, dictionary, parameters_keys=None):
    measurement_list = get_measurement_list(machine_type, dictionary, parameters_keys=parameters_keys)
    modbus_measurement_list = get_modbus_measurement_list(machine_type, dictionary, parameters_keys=parameters_keys)
    function_measurement_list = get_function_measurement_list(machine_type, dictionary, parameters_keys=parameters_keys)
    # adam_measurement_list = get_adam_measurement_list(machine_type, dictionary, parameters_keys=parameters_keys)
    return measurement_list + modbus_measurement_list + function_measurement_list # + adam_measurement_list


def get_measurement_list(machine_type, dictionary, prefix='MEASUREMENT_', parameters_keys=None):
    import library.measurement
    measurement_list = []
    for key in sorted(dictionary): # sorted(dictionary) returns a list of keys sorted alphabetically
        if key.startswith(prefix):
            try:
                # dictionary[key] is a dictionary in string
                measurement_dict = json.loads(dictionary[key])
                sensor_type = list(measurement_dict.keys())[0]
                m = library.measurement.Measurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
                measurement_list.append(m)
            except Exception as e:
                logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
                logging.getLogger().debug(e, exc_info=True) 
                pass
    return measurement_list


def get_modbus_measurement_list(machine_type, dictionary, prefix='MODBUS_MEASUREMENT_', parameters_keys=None):
    import library.measurement
    measurement_list = []
    for key in sorted(dictionary): # sorted(dictionary) returns a list of keys sorted alphabetically
        if key.startswith(prefix):
            try:
                # dictionary[key] is a dictionary in string
                measurement_dict = json.loads(dictionary[key])
                sensor_type = list(measurement_dict.keys())[0]
                measurement = library.measurement.ModbusMeasurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
                measurement_list.append(measurement)
            except Exception as e:
                logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
                logging.getLogger().debug(e, exc_info=True) 
    return measurement_list


def get_function_measurement_list(machine_type, dictionary, prefix='FUNCTION_MEASUREMENT_', parameters_keys=None):
    import library.measurement
    measurement_list = []
    for key in sorted(dictionary): # sorted(dictionary) returns a list of keys sorted alphabetically
        if key.startswith(prefix):
            try:
                # dictionary[key] is a dictionary in string
                measurement_dict = json.loads(dictionary[key])
                sensor_type = list(measurement_dict.keys())[0]
                measurement = library.measurement.FunctionMeasurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
                measurement_list.append(measurement)
            except Exception as e:
                logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
                logging.getLogger().debug(e, exc_info=True) 
    return measurement_list


def get_adam_measurement_list(machine_type, dictionary, prefix='ADAM_MEASUREMENT_', parameters_keys=None):
    import library.measurement
    measurement_list = []
    for key in sorted(dictionary): # sorted(dictionary) returns a list of keys sorted alphabetically
        if key.startswith(prefix):
            try:
                # dictionary[key] is a dictionary in string
                measurement_dict = json.loads(dictionary[key])
                sensor_type = list(measurement_dict.keys())[0]
                m = library.measurement.Measurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
                measurement_list.append(m)
            except Exception as e:
                logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
                logging.getLogger().debug(e, exc_info=True) 
    return measurement_list

#############################################################

def get_config_measurement_list(machine_type, dictionary, prefix='CONFIG_MEASUREMENT_', parameters_keys=None, logger=None):
    logger = logging.getLogger() if logger is None else logger

    filename = get(dictionary, 'CONFIG_FILE', None)

    logger.info(f'get_config_measurement_list::filename:{filename}')

    if filename is not None:
        config_list_from_file = get_config_measurement_list_from_file(machine_type, filename, dictionary, folder='./files', parameters_keys=None, logger=logger)
    else:
        config_list_from_file = []

    logger.info(f'get_config_measurement_list::config_list_from_file:{config_list_from_file}')
    config_dict_from_file = {m.sensor_type: m for m in config_list_from_file}

    config_list_from_dict = get_config_measurement_list_from_dict(machine_type, dictionary, prefix=prefix, parameters_keys=None, logger=logger)
    logger.info(f'get_config_measurement_list::config_list_from_dict:{config_list_from_dict}')
    config_dict_from_dict = {m.sensor_type: m for m in config_list_from_dict}

    config_dict = merge_dicts_priority(config_dict_from_dict, config_dict_from_file)

    return list(config_dict.values())
        

def get_config_measurement_list_from_dict(machine_type, dictionary, prefix='CONFIG_', parameters_keys=None, logger=None):
    logger = logging.getLogger() if logger is None else logger

    import library.measurement
    measurement_list = []
    prefix_classes_dict = {}
    prefix_classes_dict[prefix + 'MEASUREMENT_']            =   library.measurement.ConfigMeasurement
    prefix_classes_dict[prefix + 'MODBUS_MEASUREMENT_']     =   library.measurement.ConfigModbusMeasurement
    prefix_classes_dict[prefix + 'QUERY_MEASUREMENT_']      =   library.measurement.ConfigQueryMeasurement
    prefix_classes_dict[prefix + 'FUNCTION_MEASUREMENT_']   =   library.measurement.ConfigFunctionMeasurement
    for key in sorted(dictionary): # sorted(dictionary) returns a list of keys sorted alphabetically
        for p in prefix_classes_dict:
            if key.startswith(p):
                try:
                    # dictionary[key] is a dictionary in string
                    measurement_dict = json.loads(dictionary[key])
                    sensor_type = list(measurement_dict.keys())[0]
                    measurement = prefix_classes_dict[p](machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
                    measurement_list.append(measurement)
                except Exception as e:
                    logger.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
                    logger.debug(e, exc_info=True) 

        # if key.startswith(prefix + 'MEASUREMENT_'):
        #     try:
        #         # dictionary[key] is a dictionary in string
        #         measurement_dict = json.loads(dictionary[key])
        #         sensor_type = list(measurement_dict.keys())[0]
        #         measurement = library.measurement.ConfigMeasurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
        #         measurement_list.append(measurement)
        #     except Exception as e:
        #         logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
        #         logging.getLogger().debug(e, exc_info=True) 
        # elif key.startswith(prefix + 'MODBUS_MEASUREMENT_'):
        #     try:
        #         # dictionary[key] is a dictionary in string
        #         measurement_dict = json.loads(dictionary[key])
        #         sensor_type = list(measurement_dict.keys())[0]
        #         measurement = library.measurement.ConfigModbusMeasurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
        #         measurement_list.append(measurement)
        #     except Exception as e:
        #         logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
        #         logging.getLogger().debug(e, exc_info=True) 
        # elif key.startswith(prefix + 'FUNCTION_MEASUREMENT_'):
        #     try:
        #         # dictionary[key] is a dictionary in string
        #         measurement_dict = json.loads(dictionary[key])
        #         sensor_type = list(measurement_dict.keys())[0]
        #         measurement = library.measurement.ConfigFunctionMeasurement(machine_type, sensor_type, measurement_dict[sensor_type], dictionary, parameters_keys=parameters_keys)
        #         measurement_list.append(measurement)
        #     except Exception as e:
        #         logging.critical(F'EXCLUDING MEASUREMENT: {dictionary[key]}')
        #         logging.getLogger().debug(e, exc_info=True) 

    return measurement_list


def get_config_measurement_list_from_file(machine_type, filename, common_dict, folder='./files', parameters_keys=None, logger=None):
    logger = logging.getLogger() if logger is None else logger

    import library.measurement

    common_dict_parsed = { key.replace('CONFIG_', ''): common_dict[key] for key in common_dict if key.startswith('CONFIG_') and not key.startswith ('CONFIG_MEASUREMENT_')}

    logger.info(f'get_config_measurement_list_from_file::common_dict_parsed:{common_dict_parsed}')

    measurement_list = []
    try:
        with open(os.path.join(folder, filename), 'r') as f:
            json_content = json.load(f)
            logger.info(f'get_config_measurement_list_from_file::json_content:{json_content}')

        measurement_type_class_dict = {}
        measurement_type_class_dict['MEASUREMENTS']             =  library.measurement.ConfigMeasurement
        measurement_type_class_dict['MODBUS_MEASUREMENTS']      =  library.measurement.ConfigModbusMeasurement
        measurement_type_class_dict['QUERY_MEASUREMENT']        =  library.measurement.ConfigQueryMeasurement
        measurement_type_class_dict['FUNCTION_MEASUREMENTS']    =  library.measurement.ConfigFunctionMeasurement

        for measurement_type in measurement_type_class_dict:
            if measurement_type in json_content:
                for row in json_content[measurement_type]:
                    try:
                        configuration_type = list(row.keys())[0]
                        m = measurement_type_class_dict[measurement_type](machine_type, configuration_type, row[configuration_type], common_dict_parsed, parameters_keys=parameters_keys)
                        measurement_list.append(m)
                    except Exception as e:
                        logger.critical(f'get_config_measurement_list_from_file::excluding_measurement:{row}')
                        logger.debug(e, exc_info=True) 


        # if 'MEASUREMENTS' in json_content:
        #     for row in json_content['MEASUREMENTS']:
        #         try:
        #             configuration_type = list(row.keys())[0]
        #             m = library.measurement.ConfigMeasurement(machine_type, configuration_type, row[configuration_type], common_dict_parsed, parameters_keys=parameters_keys)
        #             measurement_list.append(m)
        #         except Exception as e:
        #             logging.critical(f'get_config_measurement_list_from_file::excluding_measurement:{row}')
        #             logging.getLogger().debug(e, exc_info=True) 

        # if 'MODBUS_MEASUREMENTS' in json_content:
        #     for row in json_content['MODBUS_MEASUREMENTS']:
        #         try:
        #             configuration_type = list(row.keys())[0]
        #             m = library.measurement.ConfigModbusMeasurement(machine_type, configuration_type, row[configuration_type], common_dict_parsed, parameters_keys=parameters_keys)
        #             measurement_list.append(m)
        #         except Exception as e:
        #             logging.critical(f'get_config_measurement_list_from_file::excluding_measurement:{row}')
        #             logging.getLogger().debug(e, exc_info=True) 

        # if 'FUNCTION_MEASUREMENTS' in json_content:
        #     for row in json_content['FUNCTION_MEASUREMENTS']:
        #         try:
        #             configuration_type = list(row.keys())[0]
        #             m = library.measurement.ConfigFunctionMeasurement(machine_type, configuration_type, row[configuration_type], common_dict_parsed, parameters_keys=parameters_keys)
        #             measurement_list.append(m)
        #         except Exception as e:
        #             logging.critical(f'get_config_measurement_list_from_file::excluding_measurement:{row}')
        #             logging.getLogger().debug(e, exc_info=True) 

    except Exception as e:
        logger.critical(f'get_config_measurement_list_from_file::error_parsing_json:{os.path.join(folder, filename)}')
        logger.debug(e, exc_info=True) 
    return measurement_list

#############################################################

def merge_dicts(*list_of_dicts):
    result = {}
    for d in list_of_dicts:
        if d is not None:
            result.update(d)
    return result


def merge_dicts_priority(first, second):
    if first is None:
        return second
    if second is None:
        return first
    # common keys of second will be overwritten by first
    return {**second, **first}


def without_keys(d, keys):
    return {k: v for k, v in d.items() if k not in keys}

#######################################################################

async def run_and_try_async(f, retry_count, delay, *args, **kwargs):
    for i in range(retry_count):
        try:
            return f(*args, **kwargs)
        except:
            logging.debug('run_and_try_if_true iteration {}'.format(i))
            if i == 0:
                logging.error(traceback.format_exc())
            await asyncio.sleep(delay)


async def run_and_try_if_true_async(f, retry_count, delay, *args, **kwargs):
    for i in range(retry_count):
        try:
            if f(*args, **kwargs):
                return True
        except:
            logging.debug('run_and_try_if_true iteration {}'.format(i))
            if i == 0:
                logging.error(traceback.format_exc())
            await asyncio.sleep(delay)
    return False


def run_and_try_sync(f, retry_count, delay, *args, **kwargs):
    for i in range(retry_count):
        try:
            return f(*args, **kwargs)
        except:
            logging.debug('run_and_try_if_true iteration {}'.format(i))
            if i == 0:
                logging.error(traceback.format_exc())
            time.sleep(delay)


def run_and_try_if_true_sync(f, retry_count, delay, *args, **kwargs):
    for i in range(retry_count):
        try:
            if f(*args, **kwargs):
                return True
        except:
            logging.debug('run_and_try_if_true iteration {}'.format(i))
            if i == 0:
                logging.error(traceback.format_exc())
            time.sleep(delay)
    return False


def get_iotedge_device_name():
    if 'EdgeHubConnectionString' in os.environ:
        EdgeHubConnectionString = os.getenv('EdgeHubConnectionString') #'IOTEDGE_MODULEID')
        # EdgeHubConnectionString is:
        # HostName=;GatewayHostName=;DeviceId=;ModuleId=;SharedAccessKey=
        iot_edge_device_name = EdgeHubConnectionString.split(';')[2].split('=')[1]
    else:
        iot_edge_device_name = os.getenv('IOTEDGE_DEVICEID')
    return iot_edge_device_name


#################################################################

def return_on_failure(value):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                return f(*args,**kwargs) 
            except Exception as e:
                logging.getLogger().debug(e, exc_info=True) 
                return value
        return applicator
    return decorate

#################################################################

def get(dictionary, key, default=None, common_dictionary=None):
    if key in dictionary:
        return dictionary[key]
    elif common_dictionary is not None and key in common_dictionary:
        return common_dictionary[key]
    return default


# IF KEY_LIST IS PRESENT RETURN THAT DICTIONARY['KEY_LIST']
# IF KEY IS PRESENT RETURN [ DICTIONARY['KEY'] ]
# ELSE RETURN DEFAULT
def get_single_or_list(dictionary, key, list_suffix="_LIST", default=None, common_dictionary=None):
    # KEY_LIST in dictionary
    if key + list_suffix in dictionary:
        return parse_list(dictionary[key + list_suffix], default=default)
    # KEY in dictionary
    if key in dictionary:
        return [ dictionary[key] ]
    # KEY_LIST in common_dictionary
    if common_dictionary is not None and key + list_suffix in common_dictionary:
        return parse_list(common_dictionary[key + list_suffix], default=default)
    # KEY in common_dictionary
    if common_dictionary is not None and key in common_dictionary:
        return [ common_dictionary[key] ]
    return default

#################################################################

def split_list(full_list, condition):
    true_list       = [x for x in full_list if condition(x)]
    false_list      = [x for x in full_list if not condition(x)]
    return true_list, false_list


#################################################################

def ping(hostname, count=1, timeout=2.):
    import library.ping_utils as ping_utils
    
    for _ in range(count):
        if ping_utils.do_one(hostname, timeout) is not None:
            return True
    
    return False
    # return subprocess.run(["ping", "-c", f"{count}", "-w", "2", hostname]).returncode == 0
    # return os.system(f"ping -c {count} -w2 {hostname} > /dev/null 2>&1") == 0

#################################################################

def compute_ranges(nums):
    # from a list of int return start and end
    # EX:   ranges([2, 3, 4, 7, 8, 9, 15])
    #       [(2, 4), (7, 9), (15, 15)]

    nums = sorted(set(nums))
    gaps = [[s, e] for s, e in zip(nums, nums[1:]) if s+1 < e]
    edges = iter(nums[:1] + sum(gaps, []) + nums[-1:])
    return list(zip(edges, edges))

#################################################################

def parse_enum(enum_class, name, upper=True, default=None):
    if name is None:
        return default

    name = name.upper() if upper else name
    if name in enum_class._member_names_:
        return enum_class[name]
        
    return default


def parse_enum_list(enum_class, names_list, upper=True, default=None):
    try:
        if names_list is None:
            return default

        parsed_list = []

        for name in names_list:
            enum_value = parse_enum(enum_class, name, upper=upper, default=None)
            if enum_value is not None:
                parsed_list.append(enum_value)

        return parsed_list
        
    except:
        return default

#################################################################

# OVERRIDES DECORATOR
def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider
    
#################################################################

# APPLICAZION JSON PER VARIABILI PLC DA FILE CSV
def add_csv2json_config(main_key:str, csv_dir:str, use_first_val_as_key:bool=True, json_dir:str=None):
    '''
    viene pasato il path pre del csv per la configurazione da aggiungere al file json
    '''
    data ={}
    # creazione del file di configurazoine se non presente.
    if (json_dir is None or not(os.path.isfile(json_dir))):
        json_dir='./config/json_'+datetime.datetime.now().strftime("%m%d%Y%H%M%S")+'.config'

    if (os.path.isfile(csv_dir)):
        #lettura da file csv
        with open(csv_dir, encoding='utf-8') as csvf:
            csvReader = csv.DictReader(csvf)
            for row in csvReader:
                _first_key= list(row.keys())[0] 
                if use_first_val_as_key:
                
                    key = list(row.values())[0] 
                else:
                    key = _first_key
                # rimozione del valore "chiave"
                del row[_first_key]
                data[key] = row
        # aggiunta dict al file json
        add_2_json(main_key, data, json_dir)



def add_2_json(key, data_dict, json_dir):
    with open(json_dir,"r") as f:
        data:dict = json.load(f)
    data[key]=data_dict
    with open(json_dir , "w") as json_write:
        json.dump(data, json_write, indent=4)



#### Creation delta time from string
def parse_delta_time(time_str)->timedelta:
    regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


def get_past_time(delta_time_str:str, dt:datetime=None, _2str:bool=False, _2str_format:str=''):
    dt = datetime.utcnow() if dt is None else dt
    tdelta = parse_delta_time(delta_time_str)
    if tdelta is None: return
    
    dt = dt - tdelta
    if _2str==False:
        return dt
    return dt.strftime("%Y/%m/%d %H:%M:%S")

def get_delta_time_2_seconds(delta_time_str:str):
    tdelta = parse_delta_time(delta_time_str)
    if tdelta is None: return
    return tdelta.total_seconds()
