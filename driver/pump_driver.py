#(c) Prof.-jun. Dr.-Ing. Helge Sören Stein 2020
#this is a program for the CAT Engineering MDPS Multichannel Pump
#besides this this is also a reference implementation for a HELAO driver

import serial
import time

class pump():
    def __init__(self,conf):
            self.pumpAddr = conf['pumpAddr']
            self.pumpBlockings= {i: time.time() for i in range(14)}  # init the blockings with now
            self.ser = serial.Serial(conf['port'], conf['baud'], timeout=conf['timeout'])
            for i in range(14): #turn on all the pumps in case they are off
                self.ser.write(bytes('{},PON,1234\r'.format(self.pumpAddr[i]),'utf-8'))
                self.ser.read(1000)
            self.refreshPrimings()
                
    def isBlocked(self, pump: int):
        #this is nessesary since there is no serial command that says "pump is still pumping"
        if self.pumpBlockings[pump] >= time.time():
            return True
        else:
            return False

    def setBlock(self, pump:int, time_block:float):
        #this sets a block
        self.pumpBlockings[pump] = time_block

    #def allOn(self):
    #    self.ser.write(bytes('{},WON,1\r'.format(self.pumpAddr['all']),'utf-8'))
    #    timer = time.time()  
    #    for i in range(14):
    #        if self.pumpPrimings[i]['speed'] != 0:
    #            time_block = timer+self.pumpPrimings[i]['volume']/self.pumpPrimings[i]['speed']
    #            self.setBlock(i,time_block)
    #    self.pumpPrimings = {i: {'speed': 0, 'volume': 0} for i in range(14)}

    #def dispenseVolume(self, pump:int ,volume:int ,speed:int, stage:bool,read:bool=False,direction:int=1):
        #pump is an index 0-13 indicating the pump channel
        #volume is the volume in µL, 0 to 50000µL
        #speed is a variable going from 20µl/min to 4000µL/min
        #direction is 1 for normal and 0 for reverse

    #    self.ser.write(bytes('{},PON,1234\r'.format(self.pumpAddr[pump]),'utf-8'))
    #    self.ser.write(bytes('{},WFR,{},{}\r'.format(self.pumpAddr[pump],speed,direction),'utf-8'))
    #    self.ser.write(bytes('{},WVO,{}\r'.format(self.pumpAddr[pump],volume),'utf-8'))
        
    #    if not stage:
    #        self.ser.write(bytes('{},WON,1\r'.format(self.pumpAddr[pump]),'utf-8'))

    #        time_block = time.time()+volume/speed
    #        self.setBlock(pump,time_block)
    #    else:
    #        time_block = 0
    #        self.setBlock(pump,0)
    #        self.pumpPrimings[pump] = {'speed': speed, 'volume': volume}
    #    if read:
    #        ans = self.ser.read(1000)
    #    return ans if read else None


    def primePump(self,pump:int,volume:int,speed:int,direction:int=1,read:bool=False):
        #pump is an index 0-13 indicating the pump channel
        #volume is the volume in µL, 0 to 50000µL
        #speed is a variable going from 20µl/min to 4000µL/min
        #direction is 1 for normal and 0 for reverse
        #self.ser.write(bytes('{},PON,1234\r'.format(self.pumpAddr[pump]),'utf-8')) #everytime i call this line, the pump just replies that i didn't need to call it
        self.ser.write(bytes('{},WFR,{},{}\r'.format(self.pumpAddr[pump],speed,direction),'utf-8'))
        self.ser.write(bytes('{},WVO,{}\r'.format(self.pumpAddr[pump],volume),'utf-8'))
        self.pumpPrimings[pump] = {'direction': direction, 'speed': speed, 'volume': volume}
        return self.read() if read else None

    def runPump(self,pump:int):
        self.ser.write(bytes('{},WON,1\r'.format(self.pumpAddr[pump]),'utf-8'))
        time_block = time.time()+self.pumpPrimings[pump]['volume']/self.pumpPrimings[pump]['speed']*1.1 #10% margin for safety
        self.setBlock(pump,time_block)

    def getPrimings(self):
        return self.pumpPrimings

    #for initialization and debugging
    #i don't think this is actually working properly, 
    #seems to read out for each pump whatever i write to pump 0
    #but it doesn't affect anything practical we are trying to do now
    #i will add that i can't see anything in my code that explains this.
    #if i ever get the chance again, i would like to play some games with the pump serial commands
    #to see if i can replicate the pattern with different combinations of read commands
    def refreshPrimings(self):
        self.ser.read(1000)
        self.pumpPrimings = {i: {'direction': None, 'speed': None, 'volume': None} for i in range(14)}
        for i in range(14): #while loops shouldn't be a problem, just in case answer comes through garbled
            self.ser.write(bytes('{},RFR,1\r','utf-8'.format(self.pumpAddr[i])))
            out = self.ser.read(1000).split(b',')
            self.pumpPrimings[i]['speed'],self.pumpPrimings[i]['direction'] = int(out[5]),int(str(out[6])[2]) if out[1] == b'RFR' and out[3] == b'HS' and out[4] == b'OK' else None
            self.ser.write(bytes('{},RVO,1\r','utf-8'.format(self.pumpAddr[i])))
            out = self.ser.read(1000).split(b',')
            self.pumpPrimings[i]['volume'] = int(str(out[5])[2:-3]) if out[1] == b'RVO' and out[3] == b'HS' and out[4] == b'OK' else None
            print('pump '+str(i)+' initialized')

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
