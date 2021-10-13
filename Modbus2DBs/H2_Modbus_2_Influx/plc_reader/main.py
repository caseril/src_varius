import json
import os
import logging
import sys
from plc_module_class import PlcModuleClass
from influxdb_module_class import InfluxDBModuleClass
from plc_looper import PlcLooper
import library.utils as utils
######################################################################################################################
# Parametri di configurazione
plc_config_file = './config/plc_modbus.config'
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
    logging.getLogger("pymodbus").setLevel(logging.DEBUG)
    if stdout:
        logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logger = logging.getLogger(__name__)
    logger.info('init_logging::end')

######################################################################################################################

def connect_device(logger, plc_config_file):
    plc_modbus_client = PlcModuleClass(logger, plc_config_file)
    conn_res = plc_modbus_client.connect_device()
    return plc_modbus_client if conn_res else None


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
    plc_dictinoary = parseJsonConfig(plc_config_file)
    db_dictionary = parseJsonConfig(db_config_file)

    # Connessione al PLC tramite Modbus
    plc_modbus_client = connect_device(logger, plc_dictinoary)
    # Connessione al DB InfluxDB
    influxdb_client = InfluxDBModuleClass(logger, utils.get(db_dictionary,'INFLUXDB'))

    if plc_modbus_client is not None:
        logger.info("::PLC CONNECTED::")
        # Avvio lettura in loop delle variabili
        logger.info("::START CONTROLLING PLC::")
        # plc looper
        plc_looper = PlcLooper(plc_modbus_client, influxdb_client) 
        # avvio loop
        plc_looper.start_testing()

    logger.info("::STOP::")
    logger.info("------------------------------------------------------")

