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
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import MethodResponse, Message


import library.utils as utils
from library.base_module_class import BaseModuleClass
from library.measurement import Measurement, ModbusMeasurement, FunctionMeasurement



class BaseReaderModuleClass(BaseModuleClass):

    STATUS_OK = 200

    def __init__(self, machine_type, measurement_list):
        super().__init__()
        self.list_background_functions.append(self.command_directmethod)
        self.list_background_functions.append(self.start_reader_loop)
        self.machine_type = machine_type

        self.sleep_interval = utils.parse_float(os.getenv('SLEEP_INTERVAL', 30.), default=30.) # default 30 seconds
        self.measurement_list = measurement_list
        
    #######################################################################

    async def init_device_instance(self):
        return None

    async def connect_device(self, device_instance):
        pass

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

        device_instance = self.init_device_instance()

        await self.connect_device(device_instance)

        results = await self.process_measurements(measurement_list, device_instance)

        await self.disconnect_device(device_instance)
        return results


    async def process_measurements(self, measurement_list, *args, **kwargs):
        # the child class should call it in a function in list_background_functions
        # self.logger.info(f'process_measurements. measurement_list: {measurement_list}') ###############################################################
        results = []
        #if time is None:
        time = datetime.datetime.utcnow() 

        function_measurement_list, other_measurement_list = utils.split_list(measurement_list, lambda x: isinstance(x, FunctionMeasurement))

        # execute other_measurement_list before function_measurement_list
        for m in other_measurement_list + function_measurement_list: 
            logging.info(f'time - m.time: {time} - {m.time}. m.interval: {m.interval}') ###############################################################
            if m.time is None or abs((time - m.time).total_seconds()) >= m.interval:
                value = None
                try:
                    # if the first time has not to be skipped or it has already been skippen execute the measurement
                    if not m.skip_first or m.already_skipped:
                        if isinstance(m, FunctionMeasurement):
                            value, uom = await self.execute_function_measurement(m, measurement_list, *args, **kwargs)
                        elif isinstance(m, ModbusMeasurement):
                            value, uom = await self.execute_modbus_measurement(m, *args, **kwargs)
                        else:
                            value, uom = await self.execute_measurement(m, *args, **kwargs)
                    else:
                        m.already_skipped = True
                        m.set_value(datetime.datetime.utcnow(), None)
                except Exception as e: 
                    value = None
                    uom = None
                    self.logger.error('ERROR reading: {}'.format(m.sensor_type))
                    self.logger.debug(e, exc_info=True) 

                if value is not None and m.can_send(time, value, uom):
                    results.extend(m.get_messages_json())
        
        return results

###############################################################################################

    async def execute_measurement(self, measurement, *args, **kwargs):
        self.logger.info(f'execute_modbus_measurement : measurement: {vars(measurement)}') 

        if not self.is_simulator():
            device_instance = args[0]
            if measurement.operation == 'READ':
                value, uom = await device_instance.execute_command_str(measurement.command)
            else: # WRITE
                value, uom = await device_instance.execute_command_str_write(measurement.command, measurement.value)
        else:
            value, uom = self._execute_measurement_modbus_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'             : value: {value}') 
        return value, uom 
        

    async def execute_modbus_measurement(self, measurement, *args, **kwargs):
        self.logger.info(f'execute_modbus_measurement : measurement: {vars(measurement)}') 

        if not self.is_simulator():
            device_instance = args[0]
            if measurement.operation == 'READ':
                value = await device_instance.read_value(measurement.register_number, measurement.value_type, register_type=measurement.register_type, count=measurement.count, array_count=measurement.array_count)
            elif measurement.operation == 'DUMP':
                value = await device_instance.read_registers_in_batch(measurement.register_number, measurement.count, register_type=measurement.register_type, max_batch_size=100)
            else: # WRITE
                value = await device_instance.write_value(measurement.register_number, measurement.value_type, count=measurement.count)
            uom = measurement.uom
        else:
            value, uom = self._execute_measurement_modbus_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'             : value: {value}') 
        return value, uom 


    async def execute_function_measurement(self, measurement, measurement_list, *args, **kwargs):
        self.logger.info(f'execute_function_measurement : measurement: {vars(measurement)}') 

        if not self.is_simulator():
            value = measurement.evaluate(measurement_list)
            uom = measurement.uom
        else:
            value, uom = self._execute_measurement_function_simulator_(measurement, *args, **kwargs)

        self.logger.info(f'             : value: {value}') 
        return value, uom 
        
###############################################################################################

    async def _execute_measurement_simulator_(self, measurement, *args, **kwargs):
        return None, None
    
    async def _execute_measurement_modbus_simulator_(self, measurement, *args, **kwargs):
        return None, None

    async def _execute_measurement_function_simulator_(self, measurement, *args, **kwargs):
        return None, None
    
###############################################################################################
    
    async def get_measurement_from_command(self, command_data):
        self.logger.info(f'command_single : command_data: {command_data}')
        
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)
        measurement = Measurement(self.machine_type, command_data['COMMAND'], properties_dict=properties_dict, common_dictionary={})
        return [measurement]


    async def get_measurement_from_modbus_command(self, command_data):
        # if command_data['DEVICE'] == 'INGRID':
        register = command_data['REGISTER_NUMBER']
        name = command_data['NAME'] if 'NAME' in command_data else "REGISTER_{}".format(register)
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)

        measurement = ModbusMeasurement(self.machine_type, name, properties_dict=properties_dict, common_dictionary={})
        self.logger.critical(f'-------------------modbus measurements vars: {vars(measurement)}')
        return [measurement]


    async def get_measurement_from_function_command(self, command_data):
        # if command_data['DEVICE'] == 'INGRID':
        # function = command_data['Function']
        name = command_data['NAME'] if 'NAME' in command_data else "FUNCTION"
        properties_dict = utils.merge_dicts_priority({'SKIP_SAME_VALUE': False}, command_data)

        measurement = FunctionMeasurement(self.machine_type, name, properties_dict=properties_dict, common_dictionary={})
        self.logger.critical(f'-------------------modbus measurements vars: {vars(measurement)}')
        return [measurement]


###############################################################################################
###############################################################################################

    async def start_reader_loop(self, module_client):
        self.logger.info(f'start_reader_loop called') ###############################################################

        while True:
            if not self.is_enabled():
                await asyncio.sleep(10)
            else:
                try:
                    results = await self.process_measurement_group(self.measurement_list)

                    if len(results) > 0: 
                        self.logger.info(results)
                        await self.send_message_json(module_client, results, output='output1')
                
                except Exception as e: 
                    self.logger.error(e, exc_info=True) 
                    self.logger.debug(traceback.format_exc())

                await asyncio.sleep(self.sleep_interval)
    
###############################################################################################
###############################################################################################

    async def command_directmethod(self, module_client, output_topic='output1'):
        await utils.base_listener_directmethod(module_client, 'command', self._command_raw_, output_topic=output_topic)

###############################################################################################
###############################################################################################

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
            self.logger.info(f'command remote method received. Payload: {payload}')

            if not isinstance(payload, dict):
                data = json.loads(payload)
            else:
                data = payload

            measurement_list = []
            if 'COMMANDS' not in data: # SINGLE COMMAND SENT
                if utils.get(data, 'PROTOCOL', default='') == 'MODBUS':
                    measurement_sublist = await self.get_measurement_from_modbus_command(data)
                    # return BaseModuleClass.STATUS_OK, await self.modbus_command_single(data)
                elif utils.get(data, 'PROTOCOL', default='') == 'FUNCTION':
                    measurement_sublist = await self.get_measurement_from_function_command(data)
                else:
                    measurement_sublist = await self.get_measurement_from_command(data)
                    # return BaseModuleClass.STATUS_OK, await self.command_single(data)

                if measurement_sublist is not None:
                    measurement_list.extend(measurement_sublist)
            else:
                # results = []
                for command in data['COMMANDS']:
                    command_data = utils.merge_dicts_priority(command, utils.without_keys(data, 'COMMANDS'))
                    
                    if utils.get(command_data, 'PROTOCOL', default='') == 'MODBUS':
                        measurement_sublist = await self.get_measurement_from_modbus_command(command_data)
                        # results.append(await self.modbus_command_single(command_data))
                    elif utils.get(command_data, 'PROTOCOL', default='') == 'FUNCTION':
                        measurement_sublist = await self.get_measurement_from_function_command(command_data)
                    else:
                        measurement_sublist = await self.get_measurement_from_command(command_data)
                        # results.append(await self.command_single(command_data))

                    if measurement_sublist is not None:
                        measurement_list.extend(measurement_sublist)

            results = await self.process_measurement_group(measurement_list)
            
            self.logger.info(f'command remote method measurement_list: {measurement_list}. results: {results}') 
            return BaseModuleClass.STATUS_OK, results

        except Exception as e:
            self.logger.error('ERROR in command {}. Payload: {}. Type Payload: {}'.format(e, payload, type(payload)))
            self.logger.debug(e, exc_info=True) 
            return BaseModuleClass.STATUS_OK, traceback.format_exc()
