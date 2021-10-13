from os import write
from fastapi import FastAPI
import library.remote_methods_caller as rmc
import library.utils as utils
import logging

app = FastAPI()

@app.post("/write_measurement/{device_id}")
def itemz(device_id: str, options:dict):
    module_id = utils.get(options, 'module_id')
    method_name = utils.get(options, 'method_name')
    payload = utils.get(options, 'payload')
    done, message, code = rmc.call_direct_method(deviceID=device_id, moduleID=module_id, methodName=method_name, payload=payload)
    return {"done": done, "message": message, "code":code}

@app.get("/write_measurement/{device_id}/{module_id}/{method_name}/{measurement_name}/{write_value}")
def itemz(device_id: str, module_id:str, method_name:str, measurement_name: str, write_value: str):
    payload={measurement_name:{"VALUE": write_value}}
    print(payload)
    done, message, code = rmc.call_direct_method(deviceID=device_id, moduleID=module_id, methodName=method_name, payload=payload)
    print({"done": done, "message": message, "code":code})
    return {"done": done, "message": message, "code":code}
