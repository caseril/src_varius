import logging
import logging.handlers
import asyncio
from sartorius import Sartorius
from influxdb_module_class import InfluxDBModuleClass
import copy
from datetime import datetime




class DeviceLooper():
    def __init__(self, logger, bilancia: Sartorius, influxdb_client: InfluxDBModuleClass):
        self.bialncia = bilancia
        self.influx_client = influxdb_client
        self.logger = logger


    async def device_2_influx_db(self, device_instance, samplint_time, max_attempts):
        bkp_max_attemps=max_attempts
        while max_attempts>0:
            try:
                # lettura del valore
                try:
                    _, value = device_instance.readValue()
                    value = value if value is not None else -99.99
                    # Reset numero di tentativi
                    max_attempts=bkp_max_attemps
                except Exception as e_in:
                    self.logger.critical(f'::error: {e_in}::')
                    device_instance.connect_to_sartorius()
                    max_attempts-=1
                # scrittura dati acquisiti su influxDB
                finally:
                    asyncio.gather(self.influx_client.write_data('SARTORIUS_WEIGHT', value, datetime.utcnow().isoformat()))
            except Exception as e:
                self.logger.critical(f'::error: {e}::')
            # tempo di campionamento dal plc
            await asyncio.sleep(samplint_time)


########################################################################################################################
### MAIN STARTER

    def start(self):
        # avvio lettura da device e scrittura su db
        loop = asyncio.run(self.device_2_influx_db(self.bialncia, self.bialncia.sampling_time/1000, self.bialncia.max_attempts))
        loop.cancel()
        


            
