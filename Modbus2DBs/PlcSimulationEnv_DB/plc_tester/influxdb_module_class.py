import library.utils as utils
from influxdb import InfluxDBClient
from datetime import datetime
from enum import Enum, auto
import logging

class InputType(Enum):
    real = auto()
    simulation = auto()

class InfluxDBModuleClass:

    def __init__(self, logger, config_dict):
        self.logger = logger
        database = utils.get(config_dict, 'DATABASE')
        host = utils.get(config_dict, 'HOST')
        port = utils.get(config_dict, 'PORT')
        username = utils.get(config_dict, 'USERNAME')
        password = utils.get(config_dict, 'PASSWORD')
        ssl = str(utils.get(config_dict, 'SSL')).lower() == 'true'
        verify_ssl = str(utils.get(config_dict, 'VERIFY_SSL')).lower() == 'true'

        if username is None:
            self.client=InfluxDBClient(host=host, port=port)
        else:
            self.client = InfluxDBClient(host=host, port=port, username=username, password=password, ssl=ssl, verify_ssl=verify_ssl)
        # verifica esistenza db
        lst = self.client.get_list_database()
        check = next((item for item in lst if item["name"] == database), None)
        # ritorna l'indice:
        #index = next((i for i, item in enumerate(lst) if item["name"] == database), None)

        if(len(lst)==0 or check is None):
            self.client.create_database(database)
        self.client.switch_database(database)


    def disconnect(self):
        return self.client.close()

    def write_data(self, value, meas_name:str, value_type:str, register_number:int=None, uom:str=None, input_type:InputType=InputType.real, time=None):
        if time is None: 
            time = datetime.utcnow().isoformat()
        json_body = [
            {
                "measurement": f'{meas_name}',
                "tags": {
                    "type": f'{input_type.name}',
                    "register_number": register_number,
                    "value_type": f'{value_type}',
                    "uom": f'{uom}'
                },
                "time": f'{time}',
                "fields": {
                    "value": value
                }
            }
        ]
        self.logger.debug(f'writing::{meas_name}::value::{value}::input_type{input_type}')
        return self.client.write_points(json_body)


### Inserimento dati molteplici

    async def write_all_data(self, data_dict):
        time = datetime.utcnow().isoformat()
        json_body = []
        first:str=None
        last:str
        try:
            for d in data_dict:
                meas_name=list(d.keys())[0]
                vals=list(d.values())[0]
                register_number=utils.get(vals, 'REGISTER_NUMBER')
                value_type=utils.get(vals,'VALUE_TYPE')
                uom=utils.get(vals,'UOM')
                input_type=utils.get(vals,'INPUT_TYPE', InputType.real.name)
                value=utils.get(vals,'VALUE')

                if first is None: 
                    first=meas_name
                last = meas_name

                json_body.append({
                    "measurement": f'{meas_name}',
                    "tags": {
                        "type": f'{input_type}',
                        "register_number": register_number,
                        "value_type": f'{value_type}',
                        "uom": f'{uom}'
                    },
                    "time": f'{time}',
                    "fields": {
                        "value": value
                    }
                })
            self.logger.info(f'writing::FROM{first}::TO::{last}')
            return self.client.write_points(json_body)  
        except Exception as e:
            self.logger.error(f'error::{e}')
            return None



###############################################################################################################
### PER TEST:

if __name__ =='__main__':
    db_name = 'h2_test'
    meas_name = 'test' + datetime.utcnow().isoformat()
    value_type = 'FLOAT32'
    val = 1
    influxdb_client=InfluxDBModuleClass(None, db_name)
    res = influxdb_client.write_data(val, meas_name, value_type, InputType.simulation)
    print(res)
    result = influxdb_client.client.query(f'select value from {meas_name};')
    print("Result: {0}".format(result))

