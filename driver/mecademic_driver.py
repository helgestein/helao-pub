
import MecademicRobot
import numpy as np
from copy import copy
import time


class Mecademic:
    def __init__(self, address=None,trf=[23.75,0,73.875,0,225,0]):
        if address == None:
            address = '192.168.0.100'
        self.address = address
        self.api_robot = MecademicRobot.RobotController(self.address)
        self.connect()
        self.zeroj = [0, 0, 0, 0, 0, 0]
        self.api_robot.Home()
        self.api_robot.SetTRF(*trf)

    def connect(self):
        # Connects to the robot at initialized address and attempts to activate. Basic error handling implemented
        # Robot Controller is initialized
        self.api_robot.Connect()
        msg = self.api_robot.Activate()
        self.api_robot.Home()
        # If the robot is not properly activated attempt a self repair
        if not msg == 'Motors activated.':
            print('Noproperly activated trying self repair')
            self.auto_repair()

    def auto_repair(self):
        # If there is an error we try to autorepair it. Added an extra resume motion over the
        # mecademic suggested version
        if self.api_robot.isInError():
            self.api_robot.ResetError()
        elif self.api_robot.GetStatusRobot()['Paused'] == 1:
            self.api_robot.ResumeMotion()
        self.api_robot.ResumeMotion()
        self.api_robot.ResumeMotion()

    def set_trf(self, x, y, z, alpha, beta, gamma):
        # this sets the tool reference frame (i.e. the tip) w.r.t. to the flange reference point
        trf = [x, y, z, alpha, beta, gamma]
        self.api_robot.SetTRF(*trf)

    def mvposeplane(self, x, y):
        ppos = copy(self.api_robot.GetPose())  # plane_position: ppos
        ppos = [ppos[0] + x, ppos[1] + y, ppos[2], ppos[3], ppos[4], ppos[5]]
        ret = self.DMovePose(*ppos)
        if ret == 'End of block.':
            return True
        else:
            return False
        # implement a (relative )mv pose from the current position to a position that is offset by x,y in the same

    def DMoveJoints(self,a,b,c,d,e,f):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.05)
        self.api_robot.MoveJoints(a,b,c,d,e,f)

    def DMoveLin(self, a, b, c, d, e, f):
        print('DO NOT USE THIS FUNCTION! USE DMOVEPOSE INSTEAD THIS IS DANGEROUS!')
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.05)
        self.api_robot.MoveLin(a, b, c, d, e, f)

    def DMovePose(self, a, b, c, d, e, f):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.01)
        self.api_robot.MovePose(a, b, c, d, e, f)

    def DQLinZ(self,z=20,nsteps=100):
        pose = self.DGetPose()
        poses = np.array([pose for i in range(nsteps)])
        poses[:,2] = np.linspace(pose[2],pose[2]+z,nsteps)
        for pose in poses:
            self.DMovePose(*pose)

    def DQLinX(self,x=20,nsteps=100):
        pose = self.DGetPose()
        poses = np.array([pose for i in range(nsteps)])
        poses[:,0] = np.linspace(pose[0],pose[0]+x,nsteps)
        for pose in poses:
            self.DMovePose(*pose)

    def DQLinY(self,y=20,nsteps=100):
        pose = self.DGetPose()
        poses = np.array([pose for i in range(nsteps)])
        poses[:,1] = np.linspace(pose[1],pose[1]+y,nsteps)
        for pose in poses:
            self.DMovePose(*pose)

    def DGetPose(self):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.1)
        return copy(self.api_robot.GetPose())

    def DGetJoints(self):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.1)
        return copy(self.api_robot.GetJoints())

    def checkrobot(self):
        #this does not get a time delay
        return copy(self.api_robot.GetStatusRobot())

    def disconnect(self):
        self.api_robot.Deactivate()
        self.api_robot.Disconnect()

