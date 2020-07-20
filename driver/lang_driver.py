import sys
import clr
import time
import numpy as np
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI\_C#_VB.net")
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
 # this does not exit
# r"C:\Users\SDC_1\Documents\git\pyLang\API\LStepAPI"
#ls2 = clr.AddReference('CClassLStep')
ls = clr.AddReference('CClassLStep64') #CClassStep
import CClassLStep


class langNet():
    def __init__(self):
        self.connect()
        self.mX = 20 #4
        self.mY = 20 #20
        self.mZ = 20 #4
        self.connected = False

    def connect(self):
        self.LS = CClassLStep.LStep() #.LSX_CreateLSID(0) -> this is actually wrong
        res = self.LS.ConnectSimpleW(11, "COM4", 115200, True)
        if res == 0:
            print("Connected")
        self.LS.LoadConfigW(r"C:\Users\SDC_1\Documents\git\pyLang\config.LSControl")
        self.connected = True

    def disconnect(self):
        res = self.LS.Disconnect()
        if res == 0:
            print("Disconnected")
        self.connected = False

    def moveRelFar(self,dx,dy,dz):
        if dz > 0: #moving down -> z last
            self.moveRelXY(dx,dy)
            self.moveRelZ(dz)
        if dz <= 0: # moving up -> z first
            self.moveRelZ(dz)
            self.moveRelXY(dx,dy)

    def getPos(self):
        ans = l.LS.GetPos(0,0,0,0)
        return ans [1:-1]

    def moveRelZ(self,dz,wait=True):
        #calc how many steps:
        steps,rest = np.divmod(dz,self.mZ)
        for i in range(int(abs(steps))):
            self.LS.MoveRel(0,0,np.sign(dz)*self.mZ,0,wait)
        self.LS.MoveRel(0,0,np.sign(dz)*rest,0,wait)

    def moveRelXY(self,dx,dy,wait=True):
        #calc how many steps:
        stepdiv, rests = np.divmod([dx,dy],[self.mY,self.mX])
        steps = int(max(abs(stepdiv)))+1
        for i in range(steps):
            self.LS.MoveRel(dx/steps,dy/steps,0,0,wait)

    def moveAbsXY(self,x,y,wait=True):
        #calc how many steps:
        xp,yp,zp = self.getPos()
        dx,dy = x-xp,y-yp
        steps,rem = np.divmod(max([dx,dy]),min(self.mX,self.mY))
        #z should not change!
        xpos,ypos,zpos = np.linspace(xp,x,steps+1),np.linspace(yp,y,steps+1),np.linspace(zp,zp,steps+1)
        for x,y,z in zip(xpos[1:],ypos[1:],zpos[1:]):
            self.LS.MoveAbs(0,x,y,z,wait)
    
    def moveAbsZ(self,z,wait=True):
        #calc how many steps:
        xp,yp,zp = self.getPos()
        dz = z-zp
        steps,rem = np.divmod(dz,self.mZ)
        zpos = np.linspace(zp,z,steps+1)
        for x,y,z in zip(xpos[1:],ypos[1:],zpos[1:]):
            self.LS.MoveAbs(0,x,y,z,wait)


    def moveAbsFar(self, dx, dy, dz)
