#minimum and maximum positions are -466256 and 490711?
#or maybe 0 and 958234?
#still figuring out reference stuff
#we could put all the motors onto the same reference point
#i don't know how to reset to default
#trying to decide to what degree we should explicitly configure things

import serial
#this code is written assuming we will connect two usb ports to a single computer
#i think a master-slave connection with a single serial to the computer would be better
#but we do not have the correct cord to connect two controllers to each other

#I view this as an incredibly rough draft,
#because I do not feel that central decisions about how to implement it have been made
#almost entirely untested code
class owis:
    def __init__(self,conf):
        self.sers = []
        for ser in conf['serials']:
            self.sers.append(serial.Serial(ser['port'],ser['baud'],timeout=ser['timeout']))
        for i in range(len(self.sers)):
            self.activate(i)
            self.configure(i)

    #activate nth motor, starting from 0
    def activate(self,motor=0):
        self.sers[motor].write(bytes('INIT1\r','utf-8'))

    def configure(self,motor=0):
        self.sers[motor].write(bytes('REF1=6\r','utf-8'))

    #motor has default so that you can avoid specifying in cases where there is only a single motor
    def moveAbs(self,count,motor=0):
        self.sers[motor].write(bytes("PSET1={}\r".format(count),'utf-8'))
        self.sers[motor].write(bytes("PGO1\r",'utf-8'))

    def getPos(self):
        ret = []
        for ser in self.sers:
            ser.write(bytes("?CNT1\r",'utf-8'))
            out = ser.read(1000)
            ret.append(int(str(out)[2:-3]))
        return None if len(ret)==0 else ret[0] if len(ret)==1 else ret



