
import time
import os
import sys
import asyncio
from six.moves import input
import datetime
import json
import logging
from abc import ABC, abstractmethod
from library.plc_modbus import PlcModbus
from library.measurement import Measurement, ModbusMeasurement
import library.utils as utils
from influxdb_module_class import InfluxDBModuleClass
from multiprocessing import Process


class PlcModuleClass():

    MACHINE_TYPE = "INGRID"
    async_cmd_list=[]

    def __init__(self, logger, plc_config_dict):
        self.ip = utils.get(plc_config_dict,'MODBUS_IP')
        self.port = utils.get(plc_config_dict,'MODBUS_PORT')
        self.r_sampling_time = utils.get(plc_config_dict, 'R_SAMPLING_TIME_MS')/1000
        self.w_sampling_time = utils.get(plc_config_dict, 'W_SAMPLING_TIME_MS')/1000
        self.max_attempts=utils.get(plc_config_dict,'MAX_ATTEMPTS')
        self.measurement_list_dict = utils.get(plc_config_dict,'MODBUS_MEASUREMENTS')
        self.inputs_list_dict = utils.get(plc_config_dict, 'MODBUS_INPUTS')
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
            key=list(meas_dict.keys())[0]
            vals=list(meas_dict.values())[0]
            register_number=utils.get(vals, 'REGISTER_NUMBER')
            value_type=utils.get(vals,'VALUE_TYPE')
            uom=utils.get(vals,'UOM')
            
            self.logger.debug(f'reading::{key}::{register_number}::value type::{value_type}::uom::{uom}')
            result = await self.device_instance.read_value(register_number, value_type, register_type=None, count=None, array_count=1)
            #aggiunta del valore
            vals['VALUE']=result
        except Exception as e:
            self.logger.critical(f'error::{e}')
        return result


#############################################################################################
### SCRITTURA variabili

    def start_manual_ctrl(self):
        data = None
        while data!= -1:
            data, val = self.ask_user()
            if data is not None and isinstance(data, dict):
                register_num=utils.get(data,'REGISTER_NUMBER')
                value_type=utils.get(data,'VALUE_TYPE')
                #chiamta in asincrono
                asyncio.run(self.device_instance.write_value(register_num, value_type, val))


    def ask_user(self):
        data=None
        val=None
        print("Write value or check modbus parameters list")
        print("     - to set a value just write '<MODBUS_VARIABLE_NAME>=<VALUE>")
        print("     - to check modbus parameters list just type '--show-list'")
        print("     - to exit just type '--exit'")
        res=input('write here:')
        res=res.strip()
        if(res.lower()=='--show-list'):
            print(json.dumps(self.measurement_list_dict, indent=4, sort_keys=True))
        elif res.lower()=='--exit':
            print('ciao.')
            data=-1
        elif('=' in res):
            input_splitted=res.split('=')
            if(len(input_splitted)>1):
                key=input_splitted[0].strip()
                val=input_splitted[1].strip()
                for m in self.measurement_list_dict:
                    self.get_meas_info_from_name(key)
            else:
                print('error, retry')
        else:
            print('nada, retry')

        return data,val

    async def sample_inputs(self, data_dict):
        '''
        Inserimento dati multipli in modalità asincrona.
        '''
        if(len(data_dict)>0):
            for key, val in data_dict:
                #chiamta in sincrono
                vals = self.get_meas_info_from_name(key)
                if(vals is not None):
                    register_num=utils.get(vals,'REGISTER_NUMBER')
                    value_type=utils.get(vals,'VALUE_TYPE')
                    await self.device_instance.write_value(register_num, value_type, val)

    async def set_periodic_inputs(self, data_dict):
        '''
        dict defined as:
        REGISTER_NUMBER
        VALUE_TYPE
        SAMPLING_TIME [ms]
        '''
        while(len(data_dict)>0):
            for key, val in data_dict:
                #chiamta in sincrono
                vals = self.get_meas_info_from_name(key)
                if(vals is not None):
                    register_num=utils.get(vals,'REGISTER_NUMBER')
                    value_type=utils.get(vals,'VALUE_TYPE')
                    sampling_time=utils.get(vals,'SAMPLING_TIME')/1000
                    asyncio.run(self.write_imput_with_delay(register_num, value_type, sampling_time, val))


    async def write_imput_with_delay(self, register_num, value_type, delay, val):
        await asyncio.sleep(delay)
        return await self.device_instance.write_value(register_num, value_type, val)


