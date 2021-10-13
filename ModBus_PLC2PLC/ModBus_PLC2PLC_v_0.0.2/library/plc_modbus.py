from pymodbus.client.sync import ModbusTcpClient
import library.utils as utils
from library.base_modbus import BaseModbus
import asyncio

class PlcModbus(BaseModbus):

    def __init__(self, logger, variables_dict=None):
        super().__init__(variables_dict=variables_dict, logger=logger)
        self.ip = utils.get(variables_dict,'MODBUS_IP', "192.168.0.1")
        self.port = utils.get(variables_dict,'MODBUS_PORT', 502)
        self.max_attempts=utils.get(variables_dict,'MAX_ATTEMPTS', 3)
        self.ping_interval = utils.get(variables_dict, 'PING_INTERVAL', 10)
        

    def connect(self):
        self.client = ModbusTcpClient(self.ip, self.port, id = self.modbus_id)
        connected = self.client.connect()
        return connected

    def disconnect(self):
        return self.client.close()


    async def periodic_ping(self):
        while True:
            if utils.ping(self.ip):
                self.logger.debug(f'PING::{self.ip}:{self.port}::RECEIVED')
            else:
                self.logger.debug(f'PING::{self.ip}:{self.port}::REFUSED')
            await asyncio.sleep(self.ping_interval)
