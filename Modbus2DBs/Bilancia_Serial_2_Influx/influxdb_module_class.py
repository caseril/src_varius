import library.utils as utils
from influxdb import InfluxDBClient
from enum import Enum, auto

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

### Inserimento dati molteplici

    async def write_data(self, meas_name, value, time=None):
        try:
            value = value if value is not None else 0
            json_body=[]
            json_body.append({
                        "measurement": f'{meas_name}',
                        "time": f'{time}',
                        "fields": {"value": value}})
            result =  self.client.write_points(json_body)
            return result
        except Exception as e:
            self.logger.error(f'error::{e}')
            return None

    async def write_all_data(self, data_dict):
        '''
        Le variabili passate devono avere un parametro di valore denominato VALUE e un parametro di tempo denominato TIME
        '''
        json_body = []
        first:str=None
        last:str
        try:
            for d in data_dict:
                # nomi delle chiavi
                keys=list(d.keys())
                # nome della misura
                meas_name=keys[0]
                if first is None: 
                    first=meas_name
                last = meas_name
                # acquisizione della lista dei valori
                vals=d[meas_name]
                # acquisizione del valore:
                value=vals['VALUE']
                # acquisizione del tempo
                time = vals['TIME']

                if (value is not None):
                    # correzione lista di tags del json per l'insert
                    del vals['VALUE']
                    # json 2 string
                    # json.dumps(x, indent=4, separators=(", ", " : "))

                    json_body.append({
                        "measurement": f'{meas_name}',
                        "tags": vals,
                        "time": f'{time}',
                        "fields": {
                            "value": value
                        }
                    })
            self.logger.info(f'writing::FROM::{first}::TO::{last}')
            result =  self.client.write_points(json_body)
            return result
        except Exception as e:
            self.logger.error(f'error::{e}')
            return None


