# -*- coding: utf-8 -*-

"""
Python Interface for
Sartorius Serial Interface for
CPA, GCA and GPA scales.

Originally by Robert Gieseke - robert.gieseke@gmail.com
Modified by Zhen Kang Pang - zhenkangpang@gmail.com
See LICENSE.
"""
import math
import serial
import aenum
import traceback
import library.utils as utils
import logging
import logging.handlers


class SartoriusCommands(aenum.Enum):
    _init_ = 'value command'
    BLOCK = 110, 'O'
    READ_VALUE = 120, 'P'
    READ_UOM = 130, 'P'
    READ_VALUE_AND_UOM = 135, 'P'
    UNBLOCK = 140, 'R'
    RESTART = 150, 'S'
    TARE_ZERO = 160, 'T'
    TARE_ONLY = 170, 'U'
    ZERO = 180, 'V'
    CALIBRATION_EXTERNAL = 190, 'W'
    CALIBRATION_INTERNAL = 200, 'Z'


class SartoriusError(aenum.IntEnum):
    OK = 0
    ERROR_SERIAL = 1
    ERROR_PARSE = 2
    ERROR_EMPTY = 3


class SartoriusResponseType(aenum.Enum):
    _init_ = 'value start16 count16 start22 count22'
    STRING = 0, 0, 16, 0, 22
    FLOAT = 1, 0, 11, 6, 11
    INT = 2, 0, 11, 6, 11
    UOM = 3, 11, 3, 17, 3
    FLOAT_AND_UOM = 4, 0, 14, 6, 14
    INT_AND_UOM = 5, 0, 14, 6, 14


class SartoriusResponseMode(aenum.IntEnum):
    RESPONSE_16 = 16
    RESPONSE_22 = 22
    RESPONSE_AUTO = 30


class Sartorius():
    def __init__(self, logger, config_dict):
        self.logger = logger
        self.port = utils.get(config_dict,'SERIAL_PORT', '/dev/ttyUSB0')
        self.baudrate=utils.get(config_dict,'SERIAL_BAUDRATE', 19200)
        self.bytesize=utils.get(config_dict,'SERIAL_BYTESIZE', 7)
        self.parity=utils.get(config_dict,'SERIAL_PARITY', 'N')
        self.stopbits=utils.get(config_dict,'SERIAL_STOPBITS', 1)
        self.xonxoff=True if utils.get(config_dict,'SERIAL_XONXOFF', 'True').lower() == 'true' else False
        self.timeout=utils.get(config_dict,'SERIAL_TIMEOUT', 1)
        self.sampling_time = utils.get(config_dict,'SAMPLING_TIME', 1000)
        self.max_attempts=utils.get(config_dict,'MAX_ATTEMPTS', 3)
        self.response_mode = SartoriusResponseMode.RESPONSE_AUTO
        self.ser = None

    def connect_to_sartorius(self):
        iteration = 0
        while iteration < self.max_attempts:
            try:
                self.ser = serial.Serial(self.port)
                self.ser.baudrate = self.baudrate
                self.ser.bytesize = self.bytesize
                self.ser.parity = self.parity
                self.ser.stopbits = self.stopbits
                # INDICA HENDSHAKE SOFTWARE E NON HARDWARE
                self.ser.xonxoff = self.xonxoff
                self.ser.timeout = self.timeout
                return True
            except Exception as e:
                iteration = iteration + 1
                self.logger.critical(f'Error::{e}')
        return False

    def comm(self, command, read=False, response_type=None):
        try:
            # ESC + LETTER + \r + \n
            bin_comm = chr(27) + command + chr(13) + chr(10)
            bin_comm = bin_comm.encode('ascii')
            self.ser.write(bin_comm)

            if read:
                try:
                    response = self.ser.readline()
                    response = response.decode('ascii')
                    if len(response) == 0:
                        return SartoriusError.ERROR_EMPTY, None

                    return SartoriusError.OK, self.__parse_response(response, response_type)
                except:
                    print(traceback.format_exc())
                    return SartoriusError.ERROR_PARSE, None

            return SartoriusError.OK, None

        except:
            print(traceback.format_exc())
            return SartoriusError.ERROR_SERIAL, None

    def __extract_sub_response(self, response, response_type):
        if self.response_mode == SartoriusResponseMode.RESPONSE_AUTO:
            mode = SartoriusResponseMode.RESPONSE_16 if len(response) == 16 else SartoriusResponseMode.RESPONSE_22
        else:
            mode = self.response_mode

        if mode == SartoriusResponseMode.RESPONSE_16:
            return response[response_type.start16: response_type.start16 + response_type.count16]
        else:  # if mode == SartoriusResponseMode.RESPONSE_22:
            return response[response_type.start22: response_type.start22 + response_type.count22]

    def __parse_response(self, response, response_type):
        sub_response = self.__extract_sub_response(response, response_type)

        if response_type == SartoriusResponseType.INT:
            sub_response = sub_response.replace(' ', '')
            return int(sub_response)
        elif response_type == SartoriusResponseType.FLOAT:
            sub_response = sub_response.replace(' ', '')
            return float(sub_response)
        elif response_type == SartoriusResponseType.INT_AND_UOM:
            sub_response_int = self.__extract_sub_response(response, SartoriusResponseType.INT)
            sub_response_uom = self.__extract_sub_response(response, SartoriusResponseType.UOM)
            sub_response_int = sub_response_int.replace(' ', '')
            sub_response_uom = sub_response_uom.replace(' ', '')
            return int(sub_response_int), sub_response_uom
        elif response_type == SartoriusResponseType.FLOAT_AND_UOM:
            sub_response_float = self.__extract_sub_response(response, SartoriusResponseType.FLOAT)
            sub_response_uom = self.__extract_sub_response(response, SartoriusResponseType.UOM)
            sub_response_float = sub_response_float.replace(' ', '')
            sub_response_uom = sub_response_uom.replace(' ', '')
            return float(sub_response_float), sub_response_uom
        elif response_type == SartoriusResponseType.UOM:
            sub_response = sub_response.replace(' ', '')
            return sub_response
        else:
            return sub_response

    def readValue(self):
        return self.comm(SartoriusCommands.READ_VALUE.command, read=True, response_type=SartoriusResponseType.FLOAT)

    def readUom(self):
        return self.comm(SartoriusCommands.READ_UOM.command, read=True, response_type=SartoriusResponseType.UOM)

    def readValueAndUom(self):
        return self.comm(SartoriusCommands.READ_VALUE_AND_UOM.command, read=True, response_type=SartoriusResponseType.FLOAT_AND_UOM)

    def tareZero(self):
        return self.comm(SartoriusCommands.TARE_ZERO.command)

    def tare(self):
        return self.comm(SartoriusCommands.TARE_ONLY.command)

    def block(self):
        return self.comm(SartoriusCommands.BLOCK.command)

    def unblock(self):
        return self.comm(SartoriusCommands.UNBLOCK.command)

    def restart(self):
        return self.comm(SartoriusCommands.RESTART.command)

    def zero(self):
        return self.comm(SartoriusCommands.ZERO.command)

    def calibrationExternal(self):
        return self.comm(SartoriusCommands.CALIBRATION_EXTERNAL.command)

    def calibrationInternal(self):
        return self.comm(SartoriusCommands.CALIBRATION_INTERNAL.command)

    # def value(self):
    # """
    # Return displayed scale value.
    # """
    # try:
    # if self.inWaiting() == 0:
    ##print("Sending: '{}' = '{}'".format('\x1bP\r\n', bytes('\x1bP\r\n', 'ascii').hex()))
    ##print("Sending: '{}'".format(bytes('\x1bP\r\n', 'ascii').hex()))
    # self.write('\x1bP\r\n'.encode("ascii"))
    # answer = self.readline()
    ##print("Receiving: '{}' = '{}'".format(answer.decode('ascii').replace('\r\n', ''), answer.hex()))
    # answer = answer.decode("ascii")
    ##print("str: '{}'".format(answer))
    ##print(answer)
    # if len(answer) == 16: # menu code 7.2.1
    # answer = float(answer[0:11].replace(' ', ''))
    # else: # menu code 7.2.2
    # answer = float(answer[6:17].replace(' ',''))
    # return answer
    # except:
    # return math.nan

    # def display_unit(self):
    # """
    # Return unit.
    # """
    # self.write('\x1bP\r\n'.encode("ascii"))
    # answer = self.readline()
    # try:
    # answer = answer[11].strip()
    # except:
    # answer = ""
    # return answer

    # def tare(self):
    # """
    # (TARE) Key.
    # """
    # self.write('\x1bT\r\n'.encode("ascii"))

    # def block(self):
    # """
    # Block keys.
    # """
    # self.write('\x1bO\r\n'.encode("ascii"))

    # def unblock(self):
    # """
    # Unblock Keys.
    # """
    # self.write('x1bR\r\n'.encode("ascii"))

    # def restart(self):
    # """
    # Restart/self-test.
    # """
    # self.write('x1bS\r\n'.encode("ascii"))

    # def ical(self):
    # """
    # Internal calibration/adjustment.
    # """
    # self.write('x1bZ\r\n'.encode("ascii"))


if __name__ == '__main__':

    import time
    import datetime
    import matplotlib.pyplot as plt

    s = Sartorius('/dev/ttyUSB0')
    s.connect_to_sartorius()

    print('------------------------------------')
    print('s.readValue()')
    print(s.readValue())

    input("Press to continue.")

    for i in range(100):
        print('------------------------------------')
        print('s.readValueAndUom()')
        print(s.readValueAndUom())

        input("Press to continue.")

    print('------------------------------------')
    print('s.tareZero()')
    print(s.tareZero())

    input("Press to continue.")

    print('------------------------------------')
    print('s.tare()')
    print(s.tare())

    input("Press to continue.")

    print('s.block()')
    print(s.block())

    input("Press to continue.")

    print('s.unblock()')
    print(s.unblock())

    input("Press to continue.")

    print('s.restart()')
    print(s.restart())

    input("Press to continue.")

    print('s.zero()')
    print(s.zero())

    input("Press to continue.")

    print('s.calibrationInternal()')
    print(s.calibrationInternal())

    input("Press to continue.")

    print('s.calibrationExternal()')
    print(s.calibrationExternal())

    exit()

    while True:
        v = []

        starttime = time.time()
        for i in range(200):
            value = s.value()
            if not math.isnan(value):
                v.append(value)
                print('Time: {}. Lettura bilancia: {} g.'.format(datetime.datetime.now(), value))
                # time.sleep(0.01)
            else:
                raise Exception()

        endtime = time.time()
        print('Total time: {} s. Single time: {} s'.format(endtime - starttime, (endtime - starttime) / 200))

        plt.plot(v, '-o')

        plt.show()

    # print(s.display_unit())
