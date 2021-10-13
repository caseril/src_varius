import logging
import logging.handlers
import asyncio
from plc_readwrite import PlcVariableTags, PlcReadWrite
from dm_writer import DM_Wrter
import copy
from datetime import datetime



class PlcLooper():
    def __init__(self, plc_readers, writers):
        self.plc_readers = plc_readers
        self.writers = writers

    async def plc_2_plc(self, reader:PlcReadWrite):
        try:
            tasks = []
            for group in reader.measurement_list_dict:
                # Lista di task divisa per tempo di campionamento
                sampling_time       =group[PlcVariableTags.R_SAMPLING_TIME_MS.name]/1000
                measurements        =group[PlcVariableTags.MEASUREMENTS.name]
                tasks.append(self.read_write_variables( reader = reader, 
                                                        sampling_time=sampling_time, 
                                                        measurement_list_dict = measurements))
            # attesa della fine di tutti i task
            await asyncio.wait(tasks)
        except Exception as e:
            logging.critical(f'::error: {e}::')


    async def plc_ping(self):
        for p in self.plc_readers:
            if p.device_instance is not None:
                asyncio.gather(p.device_instance.periodic_ping())


    async def read_write_variables(self, reader, sampling_time, measurement_list_dict):
        while True:
            now = datetime.now()
            try:
                # lista di task di lettura divise per tempo di campionamento
                tasks = [reader.read_var_async(m) for m in measurement_list_dict]
                # attesa della fine di tutti i task
                await asyncio.wait(tasks)
                # scrittura dati acquisiti su influxDB
                asyncio.gather(self.write_variables(self.writers, copy.deepcopy(measurement_list_dict)))
            except Exception as e:
                logging.critical(f'::error: {e}::')
            # tempo di campionamento dal plc
            end_time = datetime.now()
            net_sampling_time = sampling_time - (end_time-now).microseconds/1e6
            net_sampling_time = net_sampling_time if net_sampling_time > 0 else 0
            await asyncio.sleep(sampling_time)


    async def write_variables(self, writers, measurement_list_dict):
        if len(writers)>0:
            for w in writers:
                sublist = [value for value in measurement_list_dict if list(value.keys())[0] in w.measurement_names]
                for m in [value for value in sublist if list(value.values())[0][PlcVariableTags.WRITE_VALUE.name] is not None]:
                    m_write = [v for v in w.measurement_list_dict if list(v.keys())[0] in list(m.keys())][0]
                    res = await w.write_var_async(m_write, list(m.values())[0][PlcVariableTags.WRITE_VALUE.name])
                    

########################################################################################################################
### MAIN STARTER

    def start_testing(self):
        # avvio lettura da database e scrittura su plc
        if not(len(self.plc_readers) >0 or len(self.plc_writers) >0):
            return
        loop = asyncio.get_event_loop()
        for reader in [reader for reader in self.plc_readers if reader is not None]:
            loop.create_task(self.plc_2_plc(reader = reader))
            loop.create_task(self.plc_ping())
        loop.run_forever()
        


            
