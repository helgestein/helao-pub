import serial
import time

class minipump():
    def __init__(self,conf):
            self.ser = serial.Serial(conf['port'], conf['baud'], timeout=conf['timeout'])

    def primePump(self,volume:int,speed:int,direction:int=1,read:bool=False):
        #direction is 0 for normal, 1 for reverse, though i think our pumps are set up so that 1 is the direction we normally want to use
        #flowrate must be between 0.012 and 263.5743 in µL/s
        #volume must be between 0 and 100000000 in µL
        #i can change the units if there is a problem. there are options we are not utilizing.
        self.ser.write(bytes('1,WPU,1,0,0,1.0\r','utf-8'))
        self.ser.write(bytes('1,WPI,1,1,1,1,Default\r','utf-8'))
        self.ser.write(bytes('1,WVT,1,1,0,{},Dispense\r'.format(volume),'utf-8'))
        self.ser.write(bytes('1,WFR,1,1,{},{},{}\r'.format(speed,speed,direction),'utf-8'))
        self.ser.write(bytes('1,WSC,1,1,0,0\r','utf-8'))
        return self.read() if read else None

    def runPump(self,read:bool=False):
        self.ser.write(bytes('1,EP,1\r','utf-8'))
        return self.read() if read else None

    def stopPump(self,read:bool=False):
        self.ser.write(bytes('1,PAX,0\r', 'utf-8'))
        return self.read() if read else None

    def readPump(self):
        self.read()
        ret = {'direction': None, 'speed': None, 'volume': None}
        self.ser.write(bytes('1,RFR,1,1\r','utf-8'))
        out = self.ser.read(1000).split(b',')
        ret['speed'],ret['direction'] = int(out[6]),int(out[8]) if out[1] == b'RFR' and out[4] == b'HS' and out[5] == b'OK' and out[6] == out[7] else None
        self.ser.write(bytes('1,RVT,1,1\r','utf-8'))
        out = self.ser.read(1000).split(b',')
        ret['volume'] = int(out[7]) if out[1] == b'RVT' and out[4] == b'HS' and out[5] == b'OK' and out[6] == b'0' else None
        return ret

    def read(self):
        a = self.ser.read(1000)
        ans = a.decode('utf-8','ignore').encode('utf-8')
        return ans         