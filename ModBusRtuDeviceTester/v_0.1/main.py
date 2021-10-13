import json
import os
import logging
from logging import handlers
import sys
from library.rtu_modbus import RtuModbus
import library.utils as utils
import asyncio
######################################################################################################################
### MAIN

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
# Parametri di configurazione
modbus_port         = '/dev/ttyUSB0'
modbus_id           = 1
modbus_stopbits     = 1
modbus_bytesize     = 8
modbus_baudrate     = 9600
modbus_timeout      = 1
modbus_method       = 'rtu'
modbus_parity       = 'N'
modbus_byteorder    = 'Big' 
modbus_wordorder    = 'Big'


######################################################################################################################
# MAIN
async def main():
    # Logging
    logger = logging
    init_logging(logger, 'test.log')
    
    # Connessione al RTU tramite Modbus
    rtu_modbus_client = RtuModbus(  logger, 
                                    modbus_id,
                                    modbus_port, 
                                    modbus_stopbits, 
                                    modbus_bytesize,
                                    modbus_baudrate,
                                    modbus_timeout, 
                                    modbus_method, 
                                    modbus_parity,
                                    modbus_byteorder,
                                    modbus_wordorder)

    if rtu_modbus_client.connect() == True:
        # Lettura dei valori
        try:
            register_num        = 40238
            type_str            = 'UINT16'
            array_count         = 1
            value               = True
            enable_write:bool   = False 
            read_result         = await rtu_modbus_client.read_value(register_num, type_str, array_count=array_count)
            print(read_result)


            # Scrittura dei valori
            if enable_write == True:
                write_result    = await rtu_modbus_client.write_value(register_num, type_str, value)
                print(write_result)

                read_result     = await rtu_modbus_client.read_value(register_num, type_str, array_count=array_count)
                print(read_result)
        except Exception as e:
            print(e)
        
        rtu_modbus_client.disconnect()

    logger.info("::STOP::")
    logger.info("------------------------------------------------------")




############################# Avvio TEST

if __name__ == "__main__":
    asyncio.run(main())
    

