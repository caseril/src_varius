import json
from library.base_modbus import ModbusRegisterType
import os
import logging
from logging import handlers
import sys
from library.device_modbus import TcpModbus
import library.utils as utils
import asyncio
import datetime
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
modbus_ip           = '192.168.103.158'
modbus_id           = 1
modbus_port         = 510
modbus_byteorder    = 'Big' 
modbus_wordorder    = 'Big'


######################################################################################################################
# MAIN
async def main():
    # Logging
    logger = logging
    init_logging(logger, 'test.log')
    
    # Connessione al RTU tramite Modbus
    rtu_modbus_client = TcpModbus(  logger, 
                                    modbus_ip,
                                    modbus_port,
                                    modbus_id,
                                    modbus_byteorder,
                                    modbus_wordorder)

    if rtu_modbus_client.connect() == True:
        # Lettura dei valori
        try:
            register_num        = 50
            type_str            = 'INT16'
            array_count         = 1
            register_type       = ModbusRegisterType.HOLDING
            value               = 100
            enable_write:bool   = True 
            read_result         = await rtu_modbus_client.read_value(register_num, type_str, register_type=register_type, array_count=array_count)
            print(read_result)


            # Scrittura dei valori
            if enable_write == True:
                write_result    = await rtu_modbus_client.write_value(register_num, type_str, value)
                print(write_result)

                read_result     = await rtu_modbus_client.read_value(register_num, type_str, array_count=array_count, register_type=register_type)
                print(read_result)
        except Exception as e:
            print(e)
        
        rtu_modbus_client.disconnect()

    logger.info("::STOP::")
    logger.info("------------------------------------------------------")




############################# Avvio TEST

if __name__ == "__main__":
    
    asyncio.run(main())
    

