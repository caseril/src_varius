import logging
import sys
import asyncio
from plc_module_class import PlcModuleClass
from influxdb_module_class import InfluxDBModuleClass
from mssql_module_class import MSSQLManager
from plc_looper import PlcLooper
import logging
import logging.handlers
import library.utils as utils
import json
import os
import shutil
import ntpath
import datetime

######################################################################################################################
# Parametri di configurazione
config_dir = './config'
old_config_dir = './config/old'
plc_config_file = './config/plc_modbus.config'
db_config_file = './config/db.config'
modbus_measurements_key = 'MODBUS_MEASUREMENTS'


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
### GENERAZIONE FILE DI CONFIGURAZIONE DA .CSV
def get_plc_config():
    files = [f for f in os.listdir(config_dir) if os.path.isfile(config_dir+'/'+f) and f.endswith('.csv')]
    if len(files)>0:
        #reset dei dati di configurazione de PLC
        reset_plc_config()
        for csv in files:
            utils.add_csv2json_config(modbus_measurements_key, config_dir+'/'+csv, json_dir=plc_config_file)
            #destinazione file di configurazione csv
            bkp_plc_config=old_config_dir+'/'+ntpath.basename(csv) +'.' + datetime.datetime.now().strftime("%m%d%Y%H%M%S")
            shutil.move(config_dir+'/'+csv, bkp_plc_config)


def reset_plc_config():
    with open(plc_config_file, 'r') as data_file:
        data:dict = json.load(data_file)
    #destinazione file di configurazione json
    bkp_plc_config=old_config_dir+'/'+ntpath.basename(plc_config_file) +'.' + datetime.datetime.now().strftime("%m%d%Y%H%M%S")
    #popped = data.pop(modbus_measurements_key, None)
    if modbus_measurements_key in data:
        del data[modbus_measurements_key]
    #spostamento file in backup
    shutil.move(plc_config_file, bkp_plc_config)

    with open(plc_config_file, 'w') as data_file:
        json.dump(data, data_file, indent=4)
    return data

######################################################################################################################
### MAIN

if __name__ == "__main__":
    logger = logging
    log_filename = 'test.log'
    init_logging(logger, log_filename)
    logger.info("::START::")
    logger.info("------------------------------------------------------")
    meas_ok:bool=True

    # Acquisizione dei file di configurazione
    get_plc_config()

    # Parsing delle variabili da file di configurazione.
    plc_dictinoary = parseJsonConfig(plc_config_file)
    db_dictionary = parseJsonConfig(db_config_file)

    # Connessione al PLC tramite Modbus
    plc_modbus_client = connect_device(logger, plc_dictinoary)
    # Connessione al DB InfluxDB
    influxdb_client = InfluxDBModuleClass(logger, utils.get(db_dictionary,'INFLUXDB'))
    # Connessione al DB MSSQLServer
    mssqldb_client = MSSQLManager(logger=logger, config_dict=utils.get(db_dictionary,'MSSQLDB'))

    if plc_modbus_client is not None:
        logger.info("::PLC CONNECTED::")
        # Avvio lettura in loop delle variabili
        logger.info("::START CONTROLLING PLC::")
        # plc looper
        plc_looper = PlcLooper(plc_modbus_client, influxdb_client, mssqldb_client) 
        # avvio loop
        plc_looper.start_testing()

    logger.info("::STOP::")
    logger.info("------------------------------------------------------")

