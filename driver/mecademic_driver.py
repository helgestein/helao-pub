
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
        retc = dict(measurement_type="mecademic_command",
        parameters={"command": "connected"},
        data={'status':True})
        # If the robot is not properly activated attempt a self repair
        if not msg == 'Motors activated.':
            prfloat('Noproperly activated trying self repair')
            self.auto_repair()
            retc = dict(
                        measurement_type="mecademic_command",
                        parameters={"command": "not_properly_connected"},
                        data={'status': False}
                    )
            return retc
        return rect


    def auto_repair(self):
        # If there is an error we try to autorepair it. Added an extra resume motion over the
        # mecademic suggested version
        if self.api_robot.isInError():
            self.api_robot.ResetError()

        elif self.api_robot.GetStatusRobot()['Paused'] == 1:
            self.api_robot.ResumeMotion()
        self.api_robot.ResumeMotion()
        self.api_robot.ResumeMotion()
        retc = dict(
            measurement_type="mecademic_command",
            parameters={"command": "error_is_reset"},
            data={'status': True}
            )
        return rect


    def set_trf(self, x: float, y: float, z:float, alpha:float, beta:float, gamma: float):
        # this sets the tool reference frame (i.e. the tip) w.r.t. to the flange reference pofloat
        trf = [x, y, z, alpha, beta, gamma]
        self.api_robot.SetTRF(*trf)
        retc = dict(
                    measurement_type="mecademic_command",
                    parameters={"command": "tool_reference_frame", "x": x, "y": y, "z": z, "alpha": alpha, "beta": beta, "gamma": gamma},
                    data={'status': True}
                )
        return rect

    def mvposeplane(self, x: float, y: float):
        ppos = copy(self.api_robot.GetPose())  # plane_position: ppos
        ppos = [ppos[0] + x, ppos[1] + y, ppos[2], ppos[3], ppos[4], ppos[5]]
        ret = self.DMovePose(*ppos)
        if ret == 'End of block.':
            return True
        else:
            return False
        retc = dict(
                    measurement_type="mecademic_command",
                    parameters={"command": "relative_move_pos", "x": x, "y": y},
                    data={'status': True}
                )
        # implement a (relative )mv pose from the current position to a position that is offset by x,y in the same
        # plane as it is now
        return rect

    def DMoveJoints(self,a: float,b: float,c: float,d: float,e: float,f: float):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.05)
        self.api_robot.MoveJofloats(a,b,c,d,e,f)
        retc = dict(
                    measurement_type="mecademic_command",
                    parameters={"command": "move_joints", "joint1": a, "joint2": b, "joint3": c, "joint4": d, "joint5": e, "joint6": f},
                    data={'status': True}
                )
        return rect


    def DMoveLin(self, a: float, b: float, c: float, d: float, e: float, f: float):
        prfloat('DO NOT USE THIS FUNCTION! USE DMOVEPOSE INSTEAD THIS IS DANGEROUS!')
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.05)
        self.api_robot.MoveLin(a, b, c, d, e, f)
        retc = dict(
                    measurement_type="mecademic_command",
                    parameters={"command": "move_linear", "axis1": a, "axis2": b, "axis3": c, "axis4": d, "axis5": e, "axis6": f},
                    data={'status': True}
                )
        return rect

    def DMovePose(self, a: float, b: float, c: float, d: float, e: float, f: float):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.01)
        self.api_robot.MovePose(a, b, c, d, e, f)
        retc = dict(
            measurement_type="mecademic_command",
            parameters={"command": "movepose", "pos1": a, "pos2": b, "pos3": c, "pos4": d, "pos5": e, "pos6": f},
            data={'status': True}
        )
        return rect
        

    def DQLinZ(self,z: float=20.0,nsteps: float=100.0):
        pose = self.DGetPose()
        poses = np.array([pose for i in range(nsteps)])
        poses[:,2] = np.linspace(pose[2],pose[2]+z,nsteps)
        for pose in poses:
            self.DMovePose(*pose)
        retc = dict(
            measurement_type="mecademic_command",
            parameters={"command": "movepose", "pos1": a, "pos2": b, "pos3": c, "pos4": d, "pos5": e, "pos6": f},
            data={'status': True}
            )
        return rect

    def DQLinX(self,x: float=20,nsteps: float=100):
        pose = self.DGetPose()
        poses = np.array([pose for i in range(nsteps)])
        poses[:,0] = np.linspace(pose[0],pose[0]+x,nsteps)
        for pose in poses:
            self.DMovePose(*pose)

    def DQLinY(self,y: float=20,nsteps: float=100):
        pose = self.DGetPose()
        poses = np.array([pose for i in range(nsteps)])
        poses[:,1] = np.linspace(pose[1],pose[1]+y,nsteps)
        for pose in poses:
            self.DMovePose(*pose)

    def DGetPose(self):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.1)
        return copy(self.api_robot.GetPose())

    def DGetJofloats(self):
        while self.checkrobot()['EOB'] != 1:
            time.sleep(0.1)
        return copy(self.api_robot.GetJofloats())

    def checkrobot(self):
        #this does not get a time delay
        return copy(self.api_robot.GetStatusRobot())

    def disconnect(self):
        self.api_robot.Deactivate()
        self.api_robot.Disconnect()
