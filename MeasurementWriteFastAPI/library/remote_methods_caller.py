import base64
import hmac
import hashlib
import time
import requests
import urllib
import json
import os
import sys


API_VERSION = '2019-07-01-preview' # os.getenv('API_VERSION') # 
TOKEN_VALID_SECS = 365 * 24 * 60 * 60 # os.getenv('TOKEN_VALID_SECS') # 
TOKEN_FORMAT = 'SharedAccessSignature sr=%s&sig=%s&se=%s&skn=%s' # os.getenv('TOKEN_FORMAT') # 
METHOD_IOT_HUB_URL_FORMAT = 'https://{}.azure-devices.net/twins/{}/modules/{}/methods?api-version={}' # os.getenv('METHOD_IOT_HUB_URL_FORMAT') #

IOT_HUB_NAME = 'greta-simulation-iothub' # os.getenv('IOT_HUB_NAME') # 
CONNECTION_STRING = "HostName=greta-simulation-iothub.azure-devices.net;SharedAccessKeyName=service;SharedAccessKey=dPOciWBm2Dtg+TnWbTJjb67m/6JHQkGlgIOMDS3RFmU=" # os.getenv('CONNECTION_STRING') 


def generate_sas_token(connectionString):
    iotHost, keyName, keyValue = [sub[sub.index('=') + 1:] for sub in connectionString.split(";")]
    targetUri = iotHost.lower()
    expiryTime = '%d' % (time.time() + int(TOKEN_VALID_SECS))
    toSign = '%s\n%s' % (targetUri, expiryTime)
    key = base64.b64decode(keyValue.encode('utf-8'))
    signature = urllib.parse.quote(base64.b64encode(hmac.HMAC(key, toSign.encode('utf-8'), hashlib.sha256).digest())).replace('/', '%2F')
    return TOKEN_FORMAT % (targetUri, signature, expiryTime, keyName)


def call_direct_method(deviceID, moduleID, methodName, payload, retry_count=3, connection_string=None):
    connection_string = CONNECTION_STRING if connection_string is None else connection_string
    sasToken = generate_sas_token(connection_string)
    url = METHOD_IOT_HUB_URL_FORMAT.format(IOT_HUB_NAME, deviceID, moduleID, API_VERSION)

    data = {"methodName": methodName, "responseTimeoutInSeconds": 10, "payload": payload}

    for _ in range(retry_count):
        r = requests.post(url, headers={'Authorization': sasToken}, data=json.dumps(data))
        #print(r.text, r.status_code)
        if r.status_code == 200:
            return True, r.text, r.status_code
    
    #return False
    return False, r.text, r.status_code

if __name__ == "__main__":
    iot_edge_name = sys.argv[1]
    module_name = sys.argv[2]
    method_name = sys.argv[3]
    message = sys.argv[4]
    success_only = bool(sys.argv[5]) if len(sys.argv) > 5 else False

    if not success_only:
        print(f'iot_edge_name: {iot_edge_name}')
        print(f'module_name: {module_name}')
        print(f'method_name: {method_name}')
        print(f'message: {message}')

    if len(sys.argv) > 6:
        import utils 
        secret_key = sys.argv[6]
        message = json.dumps(utils.generate_message_hash(message, secret_key=secret_key))
        print(f'Message: {message}')

    success, response, status_code = call_direct_method(iot_edge_name, module_name, method_name, message, retry_count=3, connection_string=CONNECTION_STRING)
    if not success_only:
        print(f'Success: {success}')
        print(f'Status: {status_code}')
   
    if not success_only and success:
        print('Payload: \n{}'.format(json.loads(response)["payload"].replace("\\n", "\n")))

    if success_only:
        print(int(success))


