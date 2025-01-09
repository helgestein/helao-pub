import sys
import clr
import time
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI\_C#_VB.net")
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
sys.path.append(r"../config")
sys.path.append(r"../driver")
from mischbares_small import config
# r"C:\Users\SDC_1\Documents\git\pyLang\API\LStepAPI"
#ls2 = clr.AddReference('CClassLStep')
#ls = clr.AddReference('CClassLStep64') #CClassStep




class langNet():
    def __init__(self,config):
        self.port = config['port']
        self.dllpath = config['dll']
        self.dllconfigpath = config['dllconfig']
        clr.AddReference(self.dllpath)
        import CClassLStep
        self.LS = CClassLStep.LStep() #.LSX_CreateLSID(0)
        self.connected = False
        self.connect()
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

    def isMoving(self,):
        pass
    
    def moveAbsZ(self, z, wait=True):
        #raise do not use this function 
        xp,yp,zp = self.getPos()
        self.LS.MoveAbs(xp,yp,z,0,wait)


    def moveAbsFar(self, dx, dy, dz): 
        if dz > 0: #moving down -> z last
            self.moveAbsXY(dx,dy)
            self.moveAbsZ2(dz)
        if dz <= 0: # moving up -> z first
            self.moveAbsZ2(dz)
            self.moveAbsXY(dx,dy)

    def setMaxVel(self,xvel,yvel,zvel):
        self.LS.SetVel(xvel,yvel,zvel,0)


    def moveAbsZ2(self,z,wait=True):
        self.moveRelZ(z-self.getPos()[2],wait)

    def stopMove(self):
        self.LS.StopAxes()

