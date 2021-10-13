import logging
import logging.handlers
import asyncio
from plc_module_class import PlcModuleClass, PlcVariableTags
from influxdb_module_class import InfluxDBModuleClass
import copy
from datetime import datetime



class PlcLooper():
    def __init__(self, plc_client: PlcModuleClass, influxdb_client: InfluxDBModuleClass):
        self.plc_client = plc_client
        self.influx_client = influxdb_client


    async def plc_2_influx_db_variables(self, meas_dict, samplint_time):
        while True:
            now = datetime.now()
            try:
                # lista di task per la lettura dal plc in modo asincrono
                tasks = [self.plc_client.read_var_async(m) for m in meas_dict]
                # attesa della fine di tutti i task
                await asyncio.wait(tasks)
                # scrittura dati acquisiti su influxDB
                asyncio.gather(self.influx_client.write_all_data(meas_dict))
            except Exception as e:
                logging.critical(f'::error: {e}::')
            # tempo di campionamento dal plc
            end_time = datetime.now()
            net_sampling_time = samplint_time - (end_time-now).microseconds/1e6
            net_sampling_time = net_sampling_time if net_sampling_time > 0 else 0
            await asyncio.sleep(samplint_time)


########################################################################################################################
### MAIN STARTER

    def start_testing(self):
        # avvio lettura da database e scrittura su plc
        #asyncio.run(self.mssql_2_plc_variables())
        if len(self.plc_client.measurement_list_dict) <=0 :
            return
        loop = asyncio.get_event_loop()
        for group in self.plc_client.measurement_list_dict:
            sampling_time=group[PlcVariableTags.R_SAMPLING_TIME_MS.name]/1000
            measurements=group[PlcVariableTags.MEASUREMENTS.name]
            loop.create_task(self.plc_2_influx_db_variables(meas_dict=copy.deepcopy(measurements), samplint_time=copy.deepcopy(sampling_time)))
        loop.run_forever()
        


            
