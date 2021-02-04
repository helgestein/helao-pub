import serial

class pump():
    def __init__(self,conf):
            self.pumpAddr = conf['pumpAddr']
            self.ser = serial.Serial(conf['port'], conf['baud'], timeout=conf['timeout'])
                
    def primePump(self,pump:int,volume:int,speed:int,direction:int=1,read:bool=False):
        # pump is an index 0-13 indicating the pump channel
        # volume is the volume in µL, 0 to 50000µL
        # speed is a variable going from 20µl/min to 4000µL/min
        # direction is 1 for normal and 0 for reverse
        self.ser.write(bytes('{},PON,1234\r'.format(self.pumpAddr[pump]),'utf-8'))
        self.ser.write(bytes('{},WFR,{},{}\r'.format(self.pumpAddr[pump],speed,direction),'utf-8'))
        self.ser.write(bytes('{},WVO,{}\r'.format(self.pumpAddr[pump],volume),'utf-8'))
        return self.read() if read else None

    def runPump(self,pump:int,read:bool=False):
        self.ser.write(bytes('{},WON,1\r'.format(self.pumpAddr[pump]),'utf-8'))
        return self.read() if read else None

    def stopPump(self,pump:int,read:bool=False):
        # this stops a selected pump and returns the nessesary information the seed is recorded as zero and direction as -1
        self.ser.write(bytes('{},WON,0\r'.format(self.pumpAddr[pump]), 'utf-8'))
        return self.read() if read else None

    def readPump(self,pump:int):
        self.read()
        ret = {'direction': None, 'speed': None, 'volume': None}
        self.ser.write(bytes('{},RFR,1\r'.format(self.pumpAddr[pump]),'utf-8'))
        out = self.ser.read(1000).split(b',')
        ret['speed'],ret['direction'] = int(out[5]),int(str(out[6])[2]) if out[1] == b'RFR' and out[3] == b'HS' and out[4] == b'OK' else None
        self.ser.write(bytes('{},RVO,1\r'.format(self.pumpAddr[pump]),'utf-8'))
        out = self.ser.read(1000).split(b',')
        ret['volume'] = int(str(out[5])[2:-3]) if out[1] == b'RVO' and out[3] == b'HS' and out[4] == b'OK' else None
        return ret
    
    def pumpOff(self,pump:int,read:bool=False):
        self.ser.write(bytes('{},OFF,1234\r'.format(self.pumpAddr[pump]),'utf-8'))
        return self.read() if read else None

    def read(self):
        ans = []
        for i in range(100):
            a = self.ser.read(1000)
            if not a == b"":
                ans.append(a.decode('utf-8','ignore').encode('utf-8'))
            else:
                break
        return ans        

    def shutdown(self):
        for i in range(14):
            self.stopPump(i)
        self.ser.close()
