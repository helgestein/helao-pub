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


    def getPos(self):
        ans = self.LS.GetPos(0,0,0,0)
        return ans [1:-1]

    def moveRelFar(self,dx,dy,dz):
        if dz > 0: #moving down -> z last
            self.moveRelXY(dx,dy)
            self.moveRelZ(dz)
        if dz <= 0: # moving up -> z first
            self.moveRelZ(dz)
            self.moveRelXY(dx,dy)

    def moveRelZ(self,dz,wait=True):
        #calc how many steps:
        steps,rest = np.divmod(dz,self.mZ)
        steps = int(abs(steps))+ 1
        for i in range(steps):
            #self.LS.MoveRel(0,0,np.sign(dz)*self.mZ,0,wait)
            #print(self.LS.SetAccelSingleAxisTVRO(2, 0))
            #self.LS.MoveRel(0,0,np.sign(dz)*rest,0,wait)
            self.LS.MoveRel(0, 0, dz/steps, 0, wait)
            print(self.LS.GetVel(0, 0, dz/steps, 0))
            

    def moveRelXY(self,dx,dy,wait=True):
        #calc how many steps:
        stepdiv, rests = np.divmod([dx,dy],[self.mY,self.mX])
        steps = int(max(abs(stepdiv)))+1
        for i in range(steps):
            self.LS.MoveRel(dx/steps,dy/steps,0,0,wait)
            print(self.LS.GetVel(dx/steps, dy/steps, 0, 0))

    def moveAbsXY(self,x,y,wait=True):
        #calc how many steps:
        xp,yp,zp = self.getPos()
        dx,dy = x-xp,y-yp
        steps,rem = np.divmod(max([abs(dx),abs(dy)]),min(self.mX,self.mY))
        steps = int(steps)
        xpos,ypos,zpos = np.linspace(xp,x,steps+2),np.linspace(yp,y,steps+2),np.linspace(zp,zp,steps+2)
        for xm,ym,zm in zip(xpos[1:],ypos[1:],zpos[1:]):
            self.LS.MoveAbs(xm,ym,zm,0, wait)
            print(self.LS.GetVel(xm, ym, zm, 0))
    
    def moveAbsZ(self, z, wait=True):
        self.LS = CClassLStep.LStep()
        xp,yp,zp = self.getPos()
        dz = z-zp
        steps,rem = np.divmod(abs(dz),self.mZ)
        steps = int(steps)
        xpos, ypos, zpos =  np.linspace(xp,xp,steps+2), np.linspace(yp,yp,steps+2), np.linspace(zp,z,steps+2)
        for xm,ym,zm in zip(xpos[1:],ypos[1:],zpos[1:]):
            self.LS.MoveAbs(xm,ym,zm,0, wait)
            print(self.LS.GetVel(xm, ym, zm, 0))


    def moveAbsFar(self, dx, dy, dz): 
        if dz > 0: #moving down -> z last
            self.moveAbsXY(dx,dy)
            self.moveAbsZ(dz)
        if dz <= 0: # moving up -> z first
            self.moveAbsZ(dz)
            self.moveAbsXY(dx,dy)

    # get the maximum velocity 
    def maxVel(XD=1000, YD=1000, ZD= 500, AD= 250): #motor speed or velocity in rpm for rotary motor in mm/s for linear motor
        LS.GetMotorMaxVel(1000, 1000, 500, 250)

'''
# setting of maximum motor speed or velocity 
LS.SetMotorMaxVel(1000, 1000, 500, 250) # the max speed is 4006
LS.GetVel(20, 20 , 20 ,1) # read velocity values based of X, Y, Z, A
LS.SetVel(X, Y, Z, A)
# A -> Axis is calibrated and ready
LS.GetStopAccel(XD, YD, ZD, AD) # the parameters show decceleration in m/S^2
LS.SetAccelSingleAxisTVRO(2, 50.0) # means Z_axis is accelerated with 50 rp^2 # so we can set acceleration for a single TVRO axis by givving two parameters: Axis and Accel
LS.SetAccel(X, Y, Z, A)
'''