#import sys
import clr
import time
#sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI\_C#_VB.net")
#sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
#sys.path.append(r"C:\Users\SDC_1\Documents\git\pyLang\LStepAPI")
 # this does not exit
# r"C:\Users\SDC_1\Documents\git\pyLang\API\LStepAPI"
#ls2 = clr.AddReference('CClassLStep')
#ls = clr.AddReference('CClassLStep64') #CClassStep
#import CClassLStep


#units of movement are mm?

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
        #self.connected = False why?, you overwrite the value from your self.connect() call?
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
        #calc how many steps:
        #steps,rest = np.divmod(abs(dz),self.mZ)
        #steps = int(steps)+ 1
        #for i in range(steps):
            #self.LS.MoveRel(0,0,np.sign(dz)*self.mZ,0,wait)
            #print(self.LS.SetAccelSingleAxisTVRO(2, 0))
            #self.LS.MoveRel(0,0,np.sign(dz)*rest,0,wait)
        #    self.LS.MoveRel(0, 0, dz/steps, 0, wait)
        self.LS.MoveRel(0,0,dz,0,wait)
            

    def moveRelXY(self,dx,dy,wait=True):
        #calc how many steps:
        #stepdiv, rests = np.divmod([abs(dx),abs(dy)],[self.mY,self.mX])
        #steps = int(max(stepdiv))+1
        #for i in range(steps):
        #    self.LS.MoveRel(dx/steps,dy/steps,0,0,wait)
        self.LS.MoveRel(dx,dy,0,0,wait)

    def moveAbsXY(self,x,y,wait=True):
        #calc how many steps:
        xp,yp,zp = self.getPos()
        #dx,dy = x-xp,y-yp
        #steps,rem = np.divmod(max([abs(dx),abs(dy)]),min(self.mX,self.mY))
        #steps = int(steps)
        #xpos,ypos = np.linspace(xp,x,steps+2),np.linspace(yp,y,steps+2)
        #for xm,ym in zip(xpos[1:],ypos[1:]):
        #    self.LS.MoveAbs(xm,ym,zp,0, wait)
        self.LS.MoveAbs(x,y,zp,0,wait)
    
    #I know Helge is planning to add some features to the action soon
    #With that in mind, I want to say here that calling this function will likely break those features.
    #So don't call this function
    #It will reset the origin for getPos to your current location for some reason
    #I have no clue why, but no bueno
    def moveAbsZ(self, z, wait=True):
        #self.LS = CClassLStep.LStep()
        xp,yp,zp = self.getPos()
        #dz = z-zp
        #steps,rem = np.divmod(abs(dz),self.mZ)
        #steps = int(steps)
        #zpos = np.linspace(zp,z,steps+2)
        #for zm in zpos[1:]:
        #    self.LS.MoveAbs(xp,yp,zm,0, wait)
        self.LS.MoveAbs(xp,yp,z,0,wait)


    def moveAbsFar(self, dx, dy, dz): 
        if dz > 0: #moving down -> z last
            self.moveAbsXY(dx,dy)
            self.moveAbsZ2(dz)
        if dz <= 0: # moving up -> z first
            self.moveAbsZ2(dz)
            self.moveAbsXY(dx,dy)

    # get the maximum velocity
    # the speed we had previously which was too fast was 15
    # now trying it with 5
    # Helge should look at it and decide what he is comfortable with -- we could maybe go a bit faster? 
    #def getMaxVel(self,XD= 1000, YD= 1000, ZD= 500, AD= 250): #motor speed or velocity in rpm for rotary motor in mm/s for linear motor
        #what do these input values mean?
    #    return self.LS.GetVel(1000, 1000, 500, 250)[1:4]

    #def setMaxVel(self,xvel,yvel,zvel):
    #    self.LS.SetVel(xvel,yvel,zvel,0)

    #jack's gimmicky fix to moveAbsZ being broken.
    #for some reason calls to LS.MoveAbs with new z but current x and y reset the origin used for getPos to current location?
    def moveAbsZ2(self,z,wait=True):
        self.moveRelZ(z-self.getPos()[2],wait)

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