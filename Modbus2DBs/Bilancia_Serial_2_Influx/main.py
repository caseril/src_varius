import json
import os
import logging
import sys
from influxdb_module_class import InfluxDBModuleClass
from device_looper import DeviceLooper
import library.utils as utils
from sartorius import Sartorius
######################################################################################################################
# Parametri di configurazione
sartorius_config_file = './config/sartorius.config'
db_config_file = './config/db.config'


######################################################################################################################
# Initializzazione del logger #
def init_logging(logger, filename, level=logging.INFO, stdout=True, maxBytes=10000, backupCount=5):
    logging.getLogger().setLevel(logging.NOTSET)
    logging.getLogger().handlers = []

    rotatingHandler = logging.handlers.RotatingFileHandler(filename=filename, maxBytes=maxBytes, backupCount=backupCount)
    rotatingHandler.setLevel(logging.DEBUG)
    rotatingHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(rotatingHandler)

    logging.getLogger(__name__).setLevel(level)
    logging.getLogger("bilancina").setLevel(logging.DEBUG)
    if stdout:
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logger = logging.getLogger(__name__)
    logger.info('init_logging::end')


######################################################################################################################
def parseJsonConfig(file_full_path):
    #pwd = os.getcwd()
    if (os.path.isfile(file_full_path)):
        with open(file_full_path,"r") as f:
            return json.load(f)
    return None

######################################################################################################################
### MAIN

if __name__ == "__main__":
    logger = logging
    log_filename = 'test.log'
    init_logging(logger, log_filename)
    logger.info("::START::")
    logger.info("------------------------------------------------------")
    meas_ok:bool=True

    # Parsing delle variabili da file di configurazione.
    sartorius_dictinoary = parseJsonConfig(sartorius_config_file)
    db_dictionary = parseJsonConfig(db_config_file)

    # Connessione alla bilancia
    bilancia = Sartorius(logger, sartorius_dictinoary)
    # Connessione al DB InfluxDB
    #influxdb_client = InfluxDBModuleClass(logger, utils.get(db_dictionary,'INFLUXDB'))
    influxdb_client = None

    if bilancia.connect_to_sartorius():
        logger.info("::SARTORIUS CONNECTED::")
        # Avvio lettura in loop delle variabili
        logger.info("::START READING SARTORIUS::")
        # device looper
        dev_loop = DeviceLooper(logger, bilancia, influxdb_client) 
        # avvio loop
        dev_loop.start()

    logger.info("::STOP::")
    logger.info("------------------------------------------------------")

