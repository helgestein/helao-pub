#(c) Prof.-jun. Dr.-Ing. Helge Sören Stein 2020
#this is a program for the CAT Engineering MDPS Multichannel Pump
#besides this this is also a reference implementation for a HELAO driver

import serial
import time

class pump():
    def __init__(self,conf):
            self.pumpAddr = conf['pumpAddr']
            self.pumpBlockings= {i: time.time() for i in range(14)}  # init the blockings with now
            self.pumpPrimings = {i: {'speed': 0, 'volume': 0} for i in range(14)}
            self.ser = serial.Serial(port=conf['port'], baud=conf['baud'], timeout=conf['timeout'])

    def isBlocked(self, pump: int):
        #this is nessesary since there is no serial command that says "pump is still pumping"
        if self.pumpBlockings[pump] >= time.time():
            return True
        else:
            return False

    def setBlock(self, pump:int, time_block:float):
        #this sets a block
        self.pumpBlockings[pump] = time_block

    def allOn(self):
        self.ser.write(bytes('{},WON,1\r'.format(self.pumpAddr['all']),'utf-8'))
        time = time.time()  
        for i in range(14):
            if self.pumpPrimings[i]['speed'] != 0:
                time_block = time+self.pumpPrimings[i]['volume']/self.pumpPrimings[i]['speed']
                self.setBlock(i,time_block)
        self.pumpPrimings = {i: {'speed': 0, 'volume': 0} for i in range(14)}

    def dispenseVolume(self, pump:int ,volume:int ,speed:int, stage:bool,read=False,direction:int=1):
        #pump is an index 0-13 incicating the pump channel
        #volume is the volume in µL
        #speed is a variable 0-1 going from 0µl/min to 4000µL/min

        self.ser.write(bytes('{},PON,1234\r'.format(self.pumpAddr[pump]),'utf-8'))
        self.ser.write(bytes('{},WFR,{},{}\r'.format(self.pumpAddr[pump],speed,direction),'utf-8'))
        self.ser.write(bytes('{},WVO,{}\r'.format(self.pumpAddr[pump],volume),'utf-8'))
        
        if not stage:
            self.ser.write(bytes('{},WON,1\r'.format(self.pumpAddr[pump]),'utf-8'))

            time_block = time.time()+volume/speed
            self.setBlock(pump,time_block)
        else:
            time_block = 0
            self.setBlock(pump,0)
            self.pumpPrimings[i] = {'speed': speed, 'volume': volume}
        if read:
            ans = self.ser.read(1000)
        return ans if read else None

    def stopPump(self, pump:int):
        #this stops a selected pump and returns the nessesary information the seed is recorded as zero and direction as -1
        #the reason for that is that i want to indicate that we manually stopped the pump
        self.ser.write(bytes('{},WON,0\r'.format(self.pumpAddr[pump]), 'utf-8'))
        time_block = time.time()
        self.setBlock(pump,time_block)
        return time_block

    def read(self):
        ans = []
        for i in range(100):
            a = self.ser.read(1000)
            if not a == b"":
                ans.append(a)
            else:
                break
        return ans        

    def shutdown(self):
        for i in range(14):
            self.stopPump(i)
        self.ser.close()
