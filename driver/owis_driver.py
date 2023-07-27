#I have decided to init things with REF{i}=6
#thus, range of valid counts is between <0 and <960,000
#I have been told one count is 0.0001mm, which I have roughly confirmed experimentally.

import serial
import time

#this machine has a documented dll which we have in our possession,
#but which i have chosen not to use, as it doesn't offer much over the serial commands,
#and is a bit more complicated. something to bear in mind, though.

#time.sleep's are in here because only the first command is sent if you try to send a bunch at once
#probably this is something using the dll would also fix
class owis:
    def __init__(self,conf):
#this code is written assuming we will connect two usb ports to a single computer
#with two different ps10 controllers
#i think a master-slave connection between two ps10's with a single serial
#to the computer would be better, but i have been told this requires terminating connectors 
#on the unused in and out ports of the ps10's, which we do not have

#the com port a given motor is assigned to seems to depend on the order in which they are turned on.
#I have a stack of ps10's -- always turn them on slowly from the bottom up
#EDIT: use the ComPortMan software to control com port assignments
        self.sers = []
        for ser in conf['serials']:
            self.sers.append(serial.Serial(ser['port'],ser['baud'],timeout=ser['timeout']))
            time.sleep(.1)
        for i in range(len(self.sers)):
            self.sers[i].write(bytes("?ASTAT\r",'utf-8'))
            time.sleep(.1)
            out = self.sers[i].read(1000)
            if  str(out)[2] not in  ["R","T","V","P"]:
                self.setCurrents(conf['currents'][i]['drive'],conf['currents'][i]['hold'],conf['currents'][i]['mode'],i)
                self.activate(i)
                self.configure(i,6)
            if conf['safe_positions'][i] != None:
                self.move(conf['safe_positions'][i],i)
            time.sleep(.1)

    #I am trying to be clever and program all these functions so that
    #one does not need to reference which motor if there is only a single motor

    #activate nth motor, where n begins incrementing from 0
    #get it out of an error state if it is in one
    def activate(self,motor:int=0):
        time.sleep(.1)
        self.sers[motor].write(bytes('INIT1\r','utf-8'))
        time.sleep(.1)
        self.sers[motor].write(bytes("?ASTAT\r",'utf-8'))
        out = self.sers[motor].read(1000)
        if str(out)[2] == "L":
            time.sleep(.1)
            self.sers[motor].write(bytes('EFREE1\r','utf-8'))

    def configure(self,motor:int=0,ref:int=6):
        time.sleep(.1)
        self.sers[motor].write(bytes(f'REF1={ref}\r','utf-8'))
        self.isMoving(motor)

    #motor has default so that you can avoid specifying in cases where there is only a single motor
    #absol=true for absolute movement, false for relative
    def move(self,count:int,motor:int=0,absol=True):
        time.sleep(.1)
        if absol:
            self.sers[motor].write(bytes("ABSOL1\r",'utf-8'))
        else: 
            self.sers[motor].write(bytes("RELAT1\r",'utf-8'))
        time.sleep(.1)
        self.sers[motor].write(bytes("PSET1={}\r".format(count),'utf-8'))
        time.sleep(.1)
        self.sers[motor].write(bytes("PGO1\r",'utf-8'))
        self.isMoving(motor)

    #holds priority while motor is moving.
    #was thinking of modifying it to just return true while motor is moving, 
    #and then handle priority in the action, but this works for now.
    def isMoving(self,motor:int=0):
        moving = True
        while moving:
            time.sleep(.1)
            self.sers[motor].write(bytes("?ASTAT\r",'utf-8'))
            out = self.sers[motor].read(1000)
            if  str(out)[2] not in  ["T","V","P"]:
                moving = False

    def getPos(self):
        time.sleep(.1)
        ret = []
        for ser in self.sers:
            ser.write(bytes("?CNT1\r",'utf-8'))
            out = ser.read(1000)
            time.sleep(.1)
            ret.append(int(str(out)[2:-3]))
        return None if len(ret)==0 else ret[0] if len(ret)==1 else ret

    #amp must be 0 for low-current mode or 1 for high-current mode
    #drive current and hold current are given as a number between 1 and 100 -- percent of total available current in a given mode.
    #will not do anything if motor has already been activated. maybe you just need to activate motor again?
    def setCurrents(self,dri:int,hol:int,amp:int,motor:int=0):
        time.sleep(.1)
        self.sers[motor].write(bytes(f"DRICUR1={dri}\r",'utf-8'))
        time.sleep(.1)
        self.sers[motor].write(bytes(f"HOLCUR1={hol}\r",'utf-8'))
        time.sleep(.1)
        self.sers[motor].write(bytes(f"AMPSHNT1={amp}\r",'utf-8'))




