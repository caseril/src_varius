import json
import os
import logging
import sys
from plc_readwrite import PlcReadWrite, PlcRwMode
from plc_looper import PlcLooper
import library.utils as utils
from dm_writer import DM_Wrter
######################################################################################################################
# Parametri di configurazione
plc_config_file = './config/plc_modbus.config'
edge_config_file = './config/edge_device.config'


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

def get_plc_read_and_connect(logger, plc_dictionary):
    plc_read=[]
    for d in plc_dictionary:
        client = PlcReadWrite(logger, d)
        if client.connect_device():
            plc_read.append(client)
        else:
            plc_read.append(None)
    return plc_read

def get_dm_writers(logger, plc_dictionary):
    writers=[]
    for d in plc_dictionary:
        client = DM_Wrter(logger, d)
        writers.append(client)
    return writers


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
    edge_dictionary = parseJsonConfig(edge_config_file)

    # Lettori da PLC
    plc_readers = get_plc_read_and_connect(logger, plc_dictinoary)

    dm_writers = get_dm_writers(logger, edge_dictionary)

    if any(ele is None for ele in plc_readers):
        logger.error("ERROR while connecting plc_readers")
    if any(ele is None for ele in dm_writers):
        logger.error("ERROR while connecting dm_writers")
    else:
        PlcLooper(plc_readers, dm_writers).start_testing()

    # Avvio del loop di test
    

    logger.info("::STOP::")
    logger.info("------------------------------------------------------")

