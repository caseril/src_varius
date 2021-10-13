import time
import os
import asyncio
import datetime
import json
import traceback
import random

from library.base_iothub_reader_module_client import BaseIotHubReaderModuleClient
from library.base_iothub_client import IobHubRemoteMethodStatus
import library.utils as utils


class RemoteMethodsTester(BaseIotHubReaderModuleClient):

    def __init__(self):
        super().__init__(None, None)
        self.machine_type = utils.get(os.environ, 'MACHINE_TYPE', 'INGRID')
        measurement_list = utils.get_all_measurement_list(self.machine_type, os.environ)
        config_measurement_list = utils.get_config_measurement_list(self.machine_type, os.environ, logger=self.logger)

        self.measurement_list = measurement_list
        self.config_measurement_list = config_measurement_list

        self.list_background_functions.append(self.write_directmethod_listener)
        self.list_background_functions.append(self.write_directmethod_crypto_listener)


    async def init_device_instance(self):
        return None

    async def connect_device(self, device_instance):
        pass

    async def disconnect_device(self, device_instance):
        pass

    #############################################################################################

    async def write_directmethod(self, payload):
        self.logger.info('WRITE_DIRECTMETHOD TRIGGERED. Payload: {}'.format(payload))
        value = await self.log_result(payload)
        if value is not None:
            return IobHubRemoteMethodStatus.STATUS_OK, value
        else:
            self.logger.error('ERROR in WRITE_DIRECTMETHOD {}. Payload: {}.'.format(payload))
            return IobHubRemoteMethodStatus.STATUS_OK, traceback.format_exc()


    async def write_directmethod_crypto(self, payload):
        self.logger.info('WRITE_DIRECTMETHOD_CRYPTO TRIGGERED. Payload: {}'.format(payload))
        try:
            is_safe, content = utils.validate_message_hash(payload)
            if is_safe:
                value = await self.log_result(content)
                if value is not None:
                    return IobHubRemoteMethodStatus.STATUS_OK, value
                return IobHubRemoteMethodStatus.STATUS_OK, value
            else:
                return IobHubRemoteMethodStatus.STATUS_OK, 'HASH DECRYPTION FAILED'
        except Exception as e:
            self.logger.error('ERROR in WRITE_DIRECTMETHOD_CRYPTO {}. Payload: {}.'.format(e, payload))
            self.logger.debug(e, exc_info=True)
            return IobHubRemoteMethodStatus.STATUS_OK, traceback.format_exc()


    async def log_result(self, content):
        value = None
        try:
            measurement = utils.get_modbus_measurement_from_dict(content, self.machine_type)
            if measurement is not None:
                measurement.last_time_write=time.time()
                value = max(measurement.min_range, min(measurement.max_range, measurement.write_value))  # clamp between min and max

                self.logger.debug("MEASUREMENT: {}, ODO_MAX: {}, ODO_MIN: {}, VALUE: {}".format(measurement.sensor_type, measurement.max_range, measurement.min_range, value))
            else:
                return IobHubRemoteMethodStatus.STATUS_OK, f'MEASUREMENT not in content: {content}'
        except Exception as e:
            self.logger.error(e, exc_info=True)
        return value

    #############################################################################################

    async def write_directmethod_listener(self, module_client, output_topic='output1'):
        await utils.base_listener_directmethod(module_client, 'write_directmethod', self.write_directmethod, output_topic=output_topic, logger=self.logger)

    async def write_directmethod_crypto_listener(self, module_client, output_topic='output1'):
        await utils.base_listener_directmethod(module_client, 'write_directmethod_crypto', self.write_directmethod_crypto, output_topic=output_topic, logger=self.logger)
