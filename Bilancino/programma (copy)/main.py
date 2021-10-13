from sartorius import Sartorius
from ingrid_modbus import IngridModbus

import numpy as np
import os
import datetime
import time
import json
import math
import logging


def get_flow(input_dict):
    register_num = input_dict["value"]["MASSFLOW"]["REGISTER_NUMBER"]
    value_type = input_dict["value"]["MASSFLOW"]["VALUE_TYPE"]
    return register_num, value_type


if __name__ == '__main__':
    date_now = datetime.datetime.now()
    folder_path = os.path.join("results", date_now.strftime("%Y-%m-%dT%H:%M"))
    os.mkdir(folder_path)

    os.mknod(os.path.join(folder_path, "time.txt"))
    os.mknod(os.path.join(folder_path, "bilancia.txt"))
    os.mknod(os.path.join(folder_path, "portata.txt"))

    exp_duration = 5  # *60.

    with open("IngridModbusModule_3003.json") as json_file:
        modbus_json = json.load(json_file)

    logger = logging.getLogger("ingrid")

    ingrid = IngridModbus(logger, None, variables_dict=modbus_json)
    if not ingrid.connect():
        raise Exception("Ingrid not able to connect")

    bilancia = Sartorius('/dev/ttyUSB0')
    if not bilancia.connect_to_sartorius():
        raise Exception("Bilancia not able to connect")

    flow_register, flow_value_type = get_flow(modbus_json)

    for i in range(0, exp_duration):
        startime = time.time()
        time_array = np.loadtxt(os.path.join(folder_path, "time.txt"))
        bilancia_array = np.loadtxt(os.path.join(folder_path, "bilancia.txt"))
        flow_array = np.loadtxt(os.path.join(folder_path, "portata.txt"))

        try:
            time_array = np.append(time_array, datetime.datetime.now().timestamp() - date_now.timestamp())
            bilancia_value = bilancia.readValue()
            flow_value = ingrid.read_value(flow_register, flow_value_type)

            if flow_value is not None:
                flow_array = np.append(flow_array, flow_value)  # s.readValue()

            if not math.isnan(bilancia_value):
                bilancia_array = np.append(bilancia_array, bilancia_value)

        except:
            print("Wrong readed")

        np.savetxt(os.path.join(folder_path, "time.txt"), time_array)
        np.savetxt(os.path.join(folder_path, "bilancia.txt"), bilancia_array)
        np.savetxt(os.path.join(folder_path, "portata.txt"), flow_array)

        print("Run: ", i + 1, " ", round(time.time() - startime, 4), " s")
        sleeptime = 1 - (time.time() - startime)
        time.sleep(sleeptime)
