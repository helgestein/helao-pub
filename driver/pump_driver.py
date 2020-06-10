#(c) Prof.-jun. Dr.-Ing. Helge Sören Stein 2020
#this is a program for the CAT Engineering MDPS Multichannel Pump
#besides this this is also a reference implementation for a HELAO driver

import serial
import time
from pydantic import BaseModel

class pump():
    def __init__():
            #there is
            self.conf = dict(port='COM1', baud=9600, timeout=1,
                        pumpAddr={i: i + 21 for i in range(14)},  # numbering is left to right top to bottom
                        pumpBlockings={i: time.time() for i in range(14)},  # init the blockings with now
                        )
            #i set the serial connection here once
            self.ser = serial.Serial(conf['port'], conf['baud'], timeout=conf['timeout'])

    def isBlocked(self, pump: int):
        #this is nessesary since there is no serial command that says "pump is still pumping"
        if self.conf['pumpBlockings'][pump] >= time.time():
            retc = dict(
                        measurement_type="pump_command",
                        parameters={"command": "isBlocked","pump":pump},
                        data={'status':True}
                    )
            return retc
        else:
            retc = dict(
                measurement_type="pump_command",
                parameters={"command": "isBlocked"},
                data={'status': False}
            )
            return retc

    def setBlock(self, pump:int, time_block:float):
        #this sets a block
        self.conf['pumpBlockings'][pump] = time_block
        retc = dict(
            measurement_type="pump_command",
            parameters={"command": "block","time_block":time_block},
        )
        return retc


    def dispenseVolume(self, pump:int ,volume:int ,speed:int ,direction:int=1,read=False):
        #pump is an index 0-13 incicating the pump channel
        #volume is the volume in µL
        #speed is a variable 0-1 going from 0µl/min to 4000µL/min

        self.ser.write(bytes('{},PON,1234\r'.format(self.conf['pumpAddr'][pump]),'utf-8'))
        self.ser.write(bytes('{},WFR,{},{}\r'.format(self.conf['pumpAddr'][pump],speed,direction),'utf-8'))
        self.ser.write(bytes('{},WVO,{}\r'.format(self.conf['pumpAddr'][pump],volume),'utf-8'))
        self.ser.write(bytes('{},WON,1\r'.format(self.conf['pumpAddr'][pump]),'utf-8'))

        time_block = time.time()+volume/speed
        _ = setBlock(pump,time_block)

        ans = self.ser.read(1000)

        retc = dict(
            measurement_type="pump_command",
            parameters={
                "command": "dispenseVolume",
                "parameters": {
                    "volume": volume,
                    "speed": speed,
                    "pump": pump,
                    "direction": direction,
                    "time_block": time_block,
                },
            },
            data={'serial_response':ans},
        )
        return retc

    def stopPump(self, pump:int):
        #this stops a selected pump and returns the nessesary information the seed is recorded as zero and direction as -1
        #the reason for that is that i want to indicate that we manually stopped the pump
        self.ser.write(bytes('{},WON,0\r'.format(conf['pumpAddr'][pump]), 'utf-8'))
        time_block = time.time()
        _ = self.setBlock(pump,time_block)
        retc = dict(
            measurement_type="pump_command",
            parameters={
                "command": "stopPump",
                "parameters": {
                    "pump": pump,
                    'speed': 0,
                    'volume': 0,
                    'direction': -1,
                    "time_block": time_block,
                },
            },
            data=None,
        )
        return retc

    def shutdown(self):
        for i in range(14):
            self.stopPump(i)
        self.ser.close()
        retc = dict(
            measurement_type="pump_command",
            parameters={"command": "shutdown"},
            data={'data':'shutdown'}
        )
        return retc
