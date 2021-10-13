import time
import os
import sys
import asyncio
from six.moves import input
import datetime
import json
import threading
import traceback
import logging
import random
from abc import ABC, abstractmethod
# from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse, Message


import library.utils as utils
# from library.base_module_class import BaseModuleClass
from library.base_iothub_client import BaseIotHubClient, IobHubRemoteMethodStatus
from library.measurement import FunctionCheckModbus, Measurement, ModbusMeasurement, FunctionMeasurement, BitmaskMeasurement, QueryMeasurement


class BaseIotHubReaderClient(BaseIotHubClient):

    STATUS_OK = 200

    def __init__(self, machine_type, measurement_list, config_measurement_list=[], variables_dict=None):
        super().__init__(machine_type, variables_dict=variables_dict)

        self.list_background_functions.append(self.start_reader_loop)
        self.list_background_functions.append(self.start_config_reader_loop)

        self.sleep_interval         = utils.parse_float(self._get_('SLEEP_INTERVAL'),               default=30.) # default 30 seconds
        self.config_sleep_interval  = utils.parse_float(self._get_('CONFIG_SLEEP_INTERVAL'),        default=3600.) # default 30 seconds
        self.enable_db              = utils.parse_bool( self._get_('ENABLE_LOCAL_DB_CONNECTION'),   default=False) # default disabled

        self.measurement_list           = measurement_list
        self.config_measurement_list    = config_measurement_list
        
    #######################################################################

    @abstractmethod
    async def init_device_instance(self):
        return None


    @abstractmethod
    async def connect_device(self, device_instance):
        pass


    @abstractmethod
    async def disconnect_device(self, device_instance):
        pass


    #######################################################################

    def _get_measurement_from_sensor_type_(self, sensor_type):
        for m in self.measurement_list:
            if m.sensor_type == sensor_type:
                return m
        return None

###############################################################################################

    async def process_measurement_group(self, measurement_list, time=None):
        # i.e
        # - init mobdus
        # - connect
        # process_measurements
        # - clone connection
        # return results

        if self.enable_db:
            self.db_manager.connect()

        device_instance = await self.init_device_instance()

        await self.connect_device(device_instance)

        results_measurement = await self.process_measurements(measurement_list, device_instance)

        await self.disconnect_device(device_instance)

        if self.enable_db:
            self.db_manager.disconnect()

        return results_measurement


    async def process_measurements(self, measurement_list, *args, **kwargs):
        # the child class should call it in a function in list_background_functions
        # self.logger.info(f'process_measurements. measurement_list: {measurement_list}') ###############################################################
        results_measurement = []
        #if time is None:
        time = datetime.datetime.utcnow() 

        query_measurement_list,    other_measurement_list = utils.split_list(measurement_list,          lambda x: isinstance(x, QueryMeasurement))
        function_measurement_list, other_measurement_list = utils.split_list(other_measurement_list,    lambda x: isinstance(x, FunctionMeasurement))
        function_check_list, other_measurement_list       = utils.split_list(other_measurement_list,    lambda x: isinstance(x, FunctionCheckModbus))
        bitmask_measurement_list,  other_measurement_list = utils.split_list(other_measurement_list,    lambda x: isinstance(x, BitmaskMeasurement))

        # execute other_measurement_list before function_measurement_list
        for m in other_measurement_list + query_measurement_list + function_measurement_list + function_check_list + bitmask_measurement_list: 
            logging.info(f'time - m.time: {time} - {m.time}. m.interval: {m.interval}') ###############################################################
            if m.time is None or abs((time - m.time).total_seconds()) >= m.interval:
                value = None
                try:
                    # if the first time has not to be skipped or it has already been skippen execute the measurement
                    if m.enabled:
                        if not m.skip_first or m.already_skipped:
                            value, uom = await self.execute_measurement_switch(m, measurement_list, *args, **kwargs)
                        else:
                            m.already_skipped = True
                            m.set_value(datetime.datetime.utcnow(), None)
                    else:
                        self.logger.info(f'process_measurements::disabled_measurement::{m.command}')
                except Exception as e: 
                    value = None
                    uom = None
                    self.logger.error(f'process_measurements::error::sensor_type::{m.sensor_type}')
                    self.logger.debug(f'process_measurements::error::{traceback.format_exc()}')
                    # self.logger.error('ERROR reading: {}'.format(m.sensor_type))
                    # self.logger.debug(e, exc_info=True) 

                if value is not None and m.can_send(time, value, uom):
                    results_measurement.append(m) # m.get_messages_json())
        
        return results_measurement

###############################################################################################

    async def execute_measurement_switch(self, measurement, measurement_list, *args, **kwargs):
        if isinstance(measurement, BitmaskMeasurement):
            value, uom = await self.execute_bitmask_measurement(measurement, measurement_list, *args, **kwargs)
        elif isinstance(measurement, FunctionMeasurement):
            value, uom = await self.execute_function_measurement(measurement, measurement_list, *args, **kwargs)
        elif isinstance(measurement, FunctionCheckModbus):
            value, uom = await self.execute_function_check_modbus(measurement, measurement_list, *args, **kwargs)
        elif isinstance(measurement, QueryMeasurement):
            value, uom = await self.execute_query_measurement(measurement, measurement_list, *args, **kwargs)
        elif isinstance(measurement, ModbusMeasurement):
            value, uom = await self.execute_modbus_measurement(measurement, measurement_list, *args, **kwargs)
        else:
            value, uom = await self.execute_measurement(measurement, measurement_list, *args, **kwargs)
        return value, uom


    async def execute_measurement(self, measurement, measurement_list, *args, **kwargs):
        self.logger.debug(f'execute_measurement::measurement::{vars(measurement)}')

        if not self.is_simulator():
            device_instance = args[0]
            if measurement.operation == 'READ':
                value, uom = await device_instance.execute_command_str(measurement.command)
            else: # WRITE
                await self._pre_write_command_execute_(measurement, measurement_list, *args, **kwargs)
                value, uom = await device_instance.execute_command_str_write(measurement.command, measurement.write_value)
                await self._post_write_command_execute_(measurement, measurement_list, *args, **kwargs)
        else:
            value, uom = await self._execute_measurement_modbus_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'execute_measurement::{measurement.sensor_type}::{value}::{uom}')
        # self.logger.info(f'             : value: {value}') 
        return value, uom 
        

    async def execute_modbus_measurement(self, measurement, measurement_list, *args, **kwargs):
        self.logger.debug(f'execute_modbus_measurement::measurement::{vars(measurement)}')

        if not self.is_simulator():
            device_instance = args[0]
            if measurement.operation == 'READ':
                value = await device_instance.read_value(measurement.register_number, measurement.value_type, index=measurement.index, register_type=measurement.register_type, count=measurement.count, array_count=measurement.array_count)
            elif measurement.operation == 'DUMP':
                value = await device_instance.read_registers_in_batch(measurement.register_number, measurement.count, register_type=measurement.register_type, max_batch_size=100)
            else: # WRITE
                await self._pre_write_command_execute_(measurement, measurement_list, *args, **kwargs)
                value = await device_instance.write_value(measurement.register_number, measurement.value_type, measurement.write_value, count=measurement.count)
                await self._post_write_command_execute_(measurement, measurement_list, *args, **kwargs)
            uom = measurement.uom
        else:
            value, uom = await self._execute_measurement_modbus_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'execute_modbus_measurement::{measurement.sensor_type}::{value}::{uom}')
        return value, uom 


    async def execute_function_measurement(self, measurement, measurement_list, *args, **kwargs):
        self.logger.debug(f'execute_function_measurement::measurement::{vars(measurement)}')

        if not self.is_simulator():
            value = measurement.evaluate(measurement_list)
            uom = measurement.uom
        else:
            value, uom = await self._execute_measurement_function_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'execute_function_measurement::{measurement.sensor_type}::{value}::{uom}')
        return value, uom 


    async def execute_function_check_modbus(self, measurement, measurement_list, *args, **kwargs):
        self.logger.debug(f'execute_function_check::value::{vars(measurement)}')

        if not self.is_simulator():
            device_instance = args[0]
            value = measurement.evaluate(measurement_list)
            uom = measurement.uom
            # Write 2 ModBus
            output_variable = measurement.output_variable
            if output_variable is not None:
                await self._pre_write_command_execute_(output_variable, measurement_list, *args, **kwargs)
                value = await device_instance.write_value(output_variable.register_number, output_variable.value_type, value, count=output_variable.count)
                await self._post_write_command_execute_(output_variable, measurement_list, *args, **kwargs)
                self.logger.info(f'write funciton_check_modbus::{output_variable.sensor_type}::{value}::{uom}')
            else:
                self.logger.error(f'error write funciton_check_modbus::{output_variable.sensor_type}::{value}::{uom}')
        else:
            value, uom = await self._execute_check_function_simulator_(measurement, *args, **kwargs)
        self.logger.info(f'execute_function_check::{measurement.sensor_type}::{value}::{uom}')
        return value, uom 


    async def execute_query_measurement(self, measurement, measurement_list, *args, **kwargs):
        self.logger.debug(f'execute_query_measurement::measurement::{vars(measurement)}')

        if not self.is_simulator():
            if not self.enable_db:
                self.logger.critical(f'ENABLE_LOCAL_DB_CONNECTION is {self.enable_db}. Enable it to run QUERY_MEASUREMENT')
                return None, None
            value = measurement.evaluate(self.db_manager)
            uom = measurement.uom
        else:
            value, uom = await self._execute_measurement_query_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'execute_query_measurement::{measurement.sensor_type}::{value}::{uom}')
        return value, uom 


    async def execute_bitmask_measurement(self, measurement, measurement_list, *args, **kwargs):
        self.logger.debug(f'execute_bitmask_measurement::measurement::{vars(measurement)}')

        if not self.is_simulator():
            value = measurement.evaluate(measurement_list)
            uom = measurement.uom
        else:
            value, uom = await self._execute_measurement_bitmask_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'execute_bitmask_measurement::{measurement.sensor_type}::{value}::{uom}')
        return value, uom 
        
###############################################################################################

    async def _pre_write_command_execute_(self, measurement, measurement_list, *args, **kwargs):
        if measurement.pre_write_command is not None:
            self.logger.info(f'_pre_write_command_execute_::{measurement.pre_write_command}')
            pre_measurement = self._get_measurement_from_sensor_type_(measurement.pre_write_command)
            await self.execute_measurement_switch(pre_measurement, measurement_list, *args, **kwargs)


    async def _post_write_command_execute_(self, measurement, measurement_list, *args, **kwargs):
        if measurement.post_write_command is not None:
            self.logger.info(f'_post_write_command_execute_::{measurement.post_write_command}')
            pre_measurement = self._get_measurement_from_sensor_type_(measurement.post_write_command)
            await self.execute_measurement_switch(pre_measurement, measurement_list, *args, **kwargs)


###############################################################################################

    async def _execute_measurement_simulator_(self, measurement, *args, **kwargs):
        return None, None
    
    async def _execute_measurement_modbus_simulator_(self, measurement, *args, **kwargs):
        return None, None

    async def _execute_measurement_function_simulator_(self, measurement, *args, **kwargs):
        return None, None

    async def _execute_check_function_simulator_(self, measurement, *args, **kwargs):
        return None, None
    
    async def _execute_measurement_query_simulator_(self, measurement, *args, **kwargs):
        return None, None
    
    async def _execute_measurement_bitmask_simulator_(self, measurement, *args, **kwargs):
        return None, None
    
###############################################################################################
    
    async def get_measurement_from_command(self, command_data):
        self.logger.debug(f'get_measurement_from_command::command_data::{command_data}')
        
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)
        measurement = Measurement(self.machine_type, command_data['COMMAND'], properties_dict=properties_dict, common_dictionary={})

        self.logger.debug(f'get_measurement_from_command::measurement::{vars(measurement)}')
        return [measurement]


    async def get_measurement_from_modbus_command(self, command_data):
        self.logger.debug(f'get_measurement_from_modbus_command::command_data::{command_data}')

        # if command_data['DEVICE'] == 'INGRID':
        register = command_data['REGISTER_NUMBER']
        name = command_data['NAME'] if 'NAME' in command_data else "REGISTER_{}".format(register)
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)

        measurement = ModbusMeasurement(self.machine_type, name, properties_dict=properties_dict, common_dictionary={})

        self.logger.debug(f'get_measurement_from_modbus_command::measurement::{vars(measurement)}')
        return [measurement]


    async def get_measurement_from_function_command(self, command_data):
        self.logger.debug(f'get_measurement_from_function_command::command_data::{command_data}')

        # if command_data['DEVICE'] == 'INGRID':
        # function = command_data['Function']
        name = command_data['NAME'] if 'NAME' in command_data else "FUNCTION"
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)

        measurement = FunctionMeasurement(self.machine_type, name, properties_dict=properties_dict, common_dictionary={})

        self.logger.debug(f'get_measurement_from_function_command::measurement::{vars(measurement)}')
        return [measurement]


    async def get_measurement_from_query_command(self, command_data):
        self.logger.debug(f'get_measurement_from_query_command::command_data::{command_data}')

        name = command_data['NAME'] if 'NAME' in command_data else "QUERY"
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)

        measurement = QueryMeasurement(self.machine_type, name, properties_dict=properties_dict, common_dictionary={})

        self.logger.debug(f'get_measurement_from_query_command::measurement::{vars(measurement)}')
        return [measurement]


    async def get_measurement_from_bitmask_command(self, command_data):
        self.logger.debug(f'get_measurement_from_bitmask_command::command_data::{command_data}')

        name = command_data['NAME'] if 'NAME' in command_data else "BITMASK"
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)

        measurement = BitmaskMeasurement(self.machine_type, name, properties_dict=properties_dict, common_dictionary={})

        self.logger.debug(f'get_measurement_from_bitmask_command::measurement::{vars(measurement)}')
        return [measurement]


###############################################################################################
###############################################################################################

    async def start_reader_loop(self, iothub_client):
        self.logger.info(f'start_reader_loop::start') ###############################################################

        while True:
            if not self.is_enabled():
                await asyncio.sleep(10)
            else:
                try:
                    if self.measurement_list is not None and len(self.measurement_list) > 0:
                        results_measurement = await self.process_measurement_group(self.measurement_list)

                        group_masurement_by_output = self.group_measurement_list_by_output(results_measurement)

                        for output, measurements_for_output in group_masurement_by_output.items():
                            # send messages for single output
                            if len(measurements_for_output) > 0: 
                                await self.send_measurement_list(iothub_client, measurements_for_output, output)

                        # if len(results_measurement) > 0: 
                        #     self.logger.info(results_measurement)
                        #     await self.send_message_json(iothub_client, results_measurement, output='output1')
                
                except Exception as e: 
                    self.logger.error(f'start_reader_loop::error')
                    self.logger.debug(f'start_reader_loop::error::{traceback.format_exc()}')
                    # self.logger.error(e, exc_info=True) 
                    # self.logger.debug(traceback.format_exc())

                await asyncio.sleep(self.sleep_interval)
    
###############################################################################################
###############################################################################################

    async def start_config_reader_loop(self, iothub_client):
        self.logger.info(f'start_config_reader_loop::start') ###############################################################

        while True:
            if not self.is_config_enabled():
                await asyncio.sleep(10)
            else:
                try:
                    if self.config_measurement_list is not None and len(self.config_measurement_list) > 0:
                        results_measurement = await self.process_measurement_group(self.config_measurement_list)

                        if len(results_measurement) > 0: 
                            group_masurement_by_output = self.group_measurement_list_by_output(results_measurement)

                            for output, measurements_for_output in group_masurement_by_output.items():
                                if len(measurements_for_output) > 0: 
                                # send messages for single output
                                    await self.send_measurement_list(iothub_client, measurements_for_output, output)
                        else:
                            self.logger.info(f'start_config_reader_loop::results:{results_measurement}::none_or_empty') ###############################################################

                        # if len(results) > 0: 
                        #     self.logger.info(results)
                        #     await self.send_message_json(iothub_client, results, output='output1')
                        # else:
                        #     self.logger.info(f'start_config_reader_loop::results:{results}::none_or_empty') ###############################################################
                    else:
                        self.logger.info(f'start_config_reader_loop::config_measurement_list:{self.config_measurement_list}::none_or_empty') ###############################################################
                
                except Exception as e: 
                    self.logger.error(f'start_config_reader_loop::error')
                    self.logger.debug(f'start_config_reader_loop::error::{traceback.format_exc()}')
                    # self.logger.error(e, exc_info=True) 
                    # self.logger.debug(traceback.format_exc())

                await asyncio.sleep(self.config_sleep_interval)
    
###############################################################################################
###############################################################################################

    async def command_directmethod(self, iothub_client, output_topic=None):
        await utils.base_listener_directmethod(iothub_client, 'command', self._command_raw_, output_topic=output_topic, logger=self.logger)

###############################################################################################
###############################################################################################

    async def get_measurement_from_command_switch(self, data):
        measurement_sublist = None
        if utils.get(data, 'PROTOCOL', default='') == 'MODBUS':
            measurement_sublist = await self.get_measurement_from_modbus_command(data)
        elif utils.get(data, 'PROTOCOL', default='') == 'FUNCTION':
            measurement_sublist = await self.get_measurement_from_function_command(data)
        elif utils.get(data, 'PROTOCOL', default='') == 'QUERY':
            measurement_sublist = await self.get_measurement_from_query_command(data)
        elif utils.get(data, 'PROTOCOL', default='') == '':
            measurement_sublist = await self.get_measurement_from_function_command(data)
        else:
            measurement_sublist = await self.get_measurement_from_command(data)
        return measurement_sublist


    async def _command_raw_(self, payload):
        """
        {
            "DEVICE": "INGRID",
            "PROTOCOL": "MODBUS",
            "OPERATION": "READ",
            "REGISTER_NUMBER": 100,
            "VALUE_TYPE": "FLOAT32"
        }
        """
        
        
        try:
            self.logger.info(f'_command_raw_::start::payload::{payload}')

            if not isinstance(payload, dict):
                data = json.loads(payload)
            else:
                data = payload

            measurement_list = []
            if 'COMMANDS' not in data: # SINGLE COMMAND SENT
                measurement_sublist = await self.get_measurement_from_command_switch(data)

                if measurement_sublist is not None:
                    measurement_list.extend(measurement_sublist)
            else:
                # results = []
                for command in data['COMMANDS']:
                    command_data = utils.merge_dicts_priority(command, utils.without_keys(data, 'COMMANDS'))
                    
                    measurement_sublist = await self.get_measurement_from_command_switch(command_data)

                    if measurement_sublist is not None:
                        measurement_list.extend(measurement_sublist)

            results = await self.process_measurement_group(measurement_list)
            
            self.logger.info(f'_command_raw_::results::{results}') 
            return IobHubRemoteMethodStatus.STATUS_OK, results

        except Exception as e:
            self.logger.error(f'_command_raw_::error::payload::{payload}')
            self.logger.debug(f'_command_raw_::error::{traceback.format_exc()}')
            # self.logger.error('ERROR in command {}. Payload: {}. Type Payload: {}'.format(e, payload, type(payload)))
            # self.logger.debug(e, exc_info=True) 
            return IobHubRemoteMethodStatus.STATUS_OK, traceback.format_exc()

###############################################################################################
###############################################################################################

    def group_measurement_list_by_output(self, measurement_list):
        groups = {}

        for m in measurement_list:
            for output in m.output_list:
                # insert outputs in groups if missing 
                if output not in groups:
                    groups[output] = []
                # append measurement to the correspondant group
                groups[output].append(m)
        return groups
            

    async def send_measurement_list(self, iothub_client, measurement_list, output):
        if len(measurement_list) > 0: 
            results_json = []
            for m in measurement_list:
                results_json.extend(m.get_messages_json())
            
            if len(results_json) > 0: 
                self.logger.info(f"output topic: {output}")
                self.logger.info(results_json)
                await self.send_message_json(iothub_client, results_json, output=output)
        
