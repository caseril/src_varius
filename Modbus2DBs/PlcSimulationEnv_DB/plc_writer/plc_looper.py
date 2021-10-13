import logging
import sys
import asyncio
from plc_module_class import PlcModuleClass
from influxdb_module_class import InfluxDBModuleClass
from mssql_module_class import MSSQLManager, Query
import logging
import logging.handlers
import library.utils as utils
import json
import os
import shutil
import ntpath
import datetime
from datetime import datetime, timedelta
import threading
import pandas as pd
import numpy as np
import time




class PlcLooper():
    def __init__(self, plc_client: PlcModuleClass, influxdb_client: InfluxDBModuleClass, mssql_client: MSSQLManager):
        self.plc_client = plc_client
        self.influx_client = influxdb_client
        self.mssql_client = mssql_client
        self.mssql_client.init_testing()


    async def plc_2_influx_db_variables(self):
        while self.plc_client.measurement_list_dict is not None and len(self.plc_client.measurement_list_dict)>0:
            try:
                for m in self.plc_client.measurement_list_dict:
                    plc_res = await self.plc_client.read_var_async(m)
                # scrittura dati acquisiti su influxDB
                influx_res = await self.influx_client.write_all_data(self.plc_client.measurement_list_dict)
            except Exception as e:
                logging.critical(f'::error: {e}::')
            # tempo di campionamento dal plc
            await asyncio.sleep(self.plc_client.r_sampling_time)


    async def mssql_2_plc_variables(self):
        data_fr_str = 'DATA_FRAME'
        ts = int(self.plc_client.w_sampling_time)
        ts_str = str(ts)+'s'
        while self.plc_client.inputs_list_dict is not None and len(self.plc_client.inputs_list_dict)>0:
            for i in self.plc_client.inputs_list_dict:
                try:
                    meas_name=list(i.keys())[0]
                    vals=list(i.values())[0]
                    register_num=utils.get(vals,'REGISTER_NUMBER')
                    value_type=utils.get(vals,'VALUE_TYPE')
                    time_span=utils.get(vals, 'TIME_SPAN')
                    from_device:str=utils.get(vals, 'FROM_DEVICE', 'N').lower()
                    default_value=utils.get(vals, 'DEFAULT_VALUE', 0)
                    
                    if from_device == 'y' or from_device == 'yes' or from_device == 's':
                        if data_fr_str not in vals:
                            vals[data_fr_str] = pd.DataFrame()
                        if len(vals[data_fr_str].index)<2:
                            query_result = self.query_meas(meas_name, time_span, ts_str)
                            vals[data_fr_str] = query_result

                        # scrittura nel plc in modalità FIFO
                        first_df_val = vals[data_fr_str]['value'][0]
                    else:
                        first_df_val=default_value

                    res = await self.plc_client.write_imput_with_delay(register_num, value_type, 0, first_df_val)
                    # rimozione primo valore inserito
                    vals[data_fr_str]=vals[data_fr_str].iloc[1:]
                except Exception as e:
                    logging.critical(f'::error: {e}::') 
            await asyncio.sleep(int(ts))


    def query_meas(self, meas_name, time_span:str, ts:str) -> pd.DataFrame:
        dt_str =  utils.get_past_time(time_span, _2str=True)
        query_str = f"select time, value \
            from {self.mssql_client.data_source} \
            where time > '{dt_str}'\
                and machine_name  = '{self.mssql_client.machine_twin}' \
                    and sensor_type = '{meas_name}'  \
            order by time asc"
        pd= self.mssql_client.query_execute(Query(query_str), fetch = True, asdataframe=True, columns=['time','value'])
        return pd.resample(ts, on = 'time').mean()


########################################################################################################################
### MAIN STARTER

    def start_testing(self):
        # avvio lettura da database e scrittura su plc
        #asyncio.run(self.mssql_2_plc_variables())

        
        loop = asyncio.get_event_loop()
        #loop.create_task(self.mssql_2_plc_variables())
        loop.create_task(self.plc_2_influx_db_variables())
        loop.run_forever()    
