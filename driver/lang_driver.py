import sys
import clr
import time
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI\_C#_VB.net")
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
sys.path.append('../config')
 # this does not exit
from mischbares_small import config
# r"C:\Users\SDC_1\Documents\git\pyLang\API\LStepAPI"
#ls2 = clr.AddReference('CClassLStep')
#ls = clr.AddReference('CClassLStep64') #CClassStep
#import CClassLStep



class langNet():
    def __init__(self,config):
        self.port = config['port']
        self.dllpath = config['dll']
        self.dllconfigpath = config['dllconfig']
        clr.AddReference(self.dllpath)
        import CClassLStep
        self.LS = CClassLStep.LStep() #.LSX_CreateLSID(0) -> this is actually wrong
        self.connected = False
        self.connect()
        #self.mX = 20 #4
        #self.mY = 20 #20
        #self.mZ = 20 #4
        self.LS.SetVel(config['vx'],config['vy'],config['vz'],0)

    def connect(self):
        res = self.LS.ConnectSimpleW(11, self.port, 115200, True)
        if res == 0:
            print("Connected")
        self.LS.LoadConfigW(self.dllconfigpath)
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
        self.LS.MoveRel(0,0,dz,0,wait)
            

    def moveRelXY(self,dx,dy,wait=True):
        self.LS.MoveRel(dx,dy,0,0,wait)

    def moveAbsXY(self,x,y,wait=True):
        xp,yp,zp = self.getPos()
        self.LS.MoveAbs(x,y,zp,0,wait)
    
    def moveAbsZ(self, z, wait=True):
        raise hell
        xp,yp,zp = self.getPos()
        self.LS.MoveAbs(xp,yp,z,0,wait)


    def moveAbsFar(self, dx, dy, dz): 
        if dz > 0: #moving down -> z last
            self.moveAbsXY(dx,dy)
            self.moveAbsZ2(dz)
        if dz <= 0: # moving up -> z first
            self.moveAbsZ2(dz)
            self.moveAbsXY(dx,dy)


    #def getMaxVel(self,XD= 1000, YD= 1000, ZD= 500, AD= 250): #motor speed or velocity in rpm for rotary motor in mm/s for linear motor
    #    return self.LS.GetVel(1000, 1000, 500, 250)[1:4]

    def setMaxVel(self,xvel,yvel,zvel):
        self.LS.SetVel(xvel,yvel,zvel,0)


    def moveAbsZ2(self,z,wait=True):
        self.moveRelZ(z-self.getPos()[2],wait)

    def moveToHome(self):
        self.moveAbsFar(config['lang']['safe_home_pos'][0], config['lang']['safe_home_pos'][1], config['lang']['safe_home_pos'][2])
        self.getPos()
    
    def moveToWaste(self):
        self.moveAbsFar(config['lang']['safe_waste_pos'][0], config['lang']['safe_waste_pos'][1], config['lang']['safe_waste_pos'][2])
        self.getPos()
    
    def moveToSample(self):
        self.moveAbsFar(config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1], config['lang']['safe_sample_pos'][2])
        self.getPos()
    
    def removeDrop(self):
        #self.moveRelFar()
        self.moveRelFar(0, 0, config['lang']['remove_drop'][2])
        self.moveAbsFar(config['lang']['remove_drop'][0], config['lang']['remove_drop'][1], config['lang']['remove_drop'][2])
        self.getPos()

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