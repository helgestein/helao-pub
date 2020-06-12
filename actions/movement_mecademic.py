# implement common movement procedures
import sys
sys.path.append(r'../drivers')
from drivers.mecademic import Mecademic
from copy import copy
import numpy as np


# Add limit rejection
# Add orientationhelp so we can load the same platemap for every plane and it takes care of it

class Movements:
    def __init__(self, confd):
        self.driver_robot = Mecademic()
        self.zeroj = [0, 0, 0, 0, 0, 0]
        self.move_to_home()
        self.safe_sample_joints = confd['safe_sample_joints']
        self.safe_reservoir_joints = confd['safe_reservoir_joints']
        self.safe_waste_joints = confd['safe_waste_joints']
        self.sample_rotation = confd['sample_rotation']
        self.reservoir_rotation = confd['reservoir_rotation']
        self.waste_rotation = confd['waste_rotation']
        self.x_limit_sample = confd['x_limit_sample']
        self.y_limit_sample = confd['y_limit_sample']
        self.x_limit_reservoir = confd['x_limit_reservoir']
        self.y_limit_reservoir = confd['y_limit_reservoir']
        self.x_limit_waste = confd['x_limit_waste']
        self.y_limit_waste = confd['y_limit_waste']

    # Done:Refactor to rotation_matrix
    def matrix_rotation(self,theta):
        theta = np.radians(theta)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((c, -s), (s, c)))
        return R

    def move_to_home(self):
        # this moves the robot safely to ou home which is defined as all joints at 0
        self.driver_robot.DMoveJoints(*self.zeroj)

    def jogging(self, joints):
        self.driver_robot.DMoveJoints(*joints)
        print('Please jog the robot. \n dist:axis \n (i.e 0.1:x, 0.1:y or 0.1:z dist in mm)')
        print('this runs until you say exit')
        pose = copy(self.driver_robot.DGetPose())
        pjoint = copy(self.driver_robot.DGetJoints())

        while True:
            inp = input()
            if inp == 'exit':
                pose = self.driver_robot.DGetPose()
                pjoint = self.driver_robot.DGetJoints()
                break
            dist, axis = inp.split(':')
            # ok tell the robot to DMovePose by distance in axis direction
            dist = float(dist)
            if axis == 'x':
                pose_mod = copy(list(pose))
                pose_mod[0] += dist
                self.driver_robot.DMovePose(*pose_mod)
            if axis == 'y':
                pose_mod = copy(list(pose))
                pose_mod[1] += dist
                self.driver_robot.DMovePose(*pose_mod)
            if axis == 'z':
                pose_mod = copy(list(pose))
                pose_mod[2] += dist
                self.driver_robot.DMovePose(*pose_mod)
            pose = self.driver_robot.DGetPose()
            pjoint = self.driver_robot.DGetJoints()
        # move to the safe plane and then return the values
        pose_mod = copy(list(pose))
        pose_mod[2] += 20
        self.driver_robot.DMovePose(*pose_mod)
        pose = self.driver_robot.DGetPose()
        pjoint = self.driver_robot.DGetJoints()
        return pose, pjoint

    # Done: alignment to sample corner
    def align_sample(self):
        self.safe_sample_corner, self.safe_sample_joints = self.jogging(self.safe_sample_joints)

    # Done: alignment to reservoir corner @fuzhan
    def align_reservoir(self):
        self.safe_reservoir_corner, self.safe_reservoir_joints = self.jogging(self.safe_reservoir_joints)

    # Done: alignment to waste corner @fuzhan
    def align_waste(self):
        self.safe_waste_corner, self.safe_waste_joints = self.jogging(self.safe_waste_joints)

    def alignment(self):
        self.move_to_home()
        print('Sample Alignment...')
        self.align_sample()
        self.move_to_home()
        print('Reservoir Alignment...')
        self.align_reservoir()
        self.move_to_home()
        print('Waste Alignment...')
        self.align_waste()
        self.move_to_home()

    def mv2sample(self, x, y):
        if 0 <= x <= self.x_limit_sample and 0 <= y <= self.y_limit_sample:
            # robot.DMoveJoints(*self.safe_sample_joints)
            p = self.matrix_rotation(self.sample_rotation).dot(np.array((x, y)))
            safe_sample_pose = [self.safe_sample_corner[0] + p[0], self.safe_sample_corner[1] + p[1],
                                self.safe_sample_corner[2],
                                self.safe_sample_corner[3], self.safe_sample_corner[4], self.safe_sample_corner[5]]
            sample_pose = copy(safe_sample_pose)
            sample_pose[2] -= 20
            self.move_to_home()
            self.driver_robot.DMoveJoints(
                *self.safe_sample_joints)  # we will not hit anything between home and the safe sample corner
            self.driver_robot.DMovePose(*safe_sample_pose)  # don't want to hit anything
            self.driver_robot.DQLinZ(z=-20)  # need to go straight down
        else:
            #print('you are out of limitation')
            raise Exception('you are out of boundary')

    def mv2reservoir(self, x, y):
        if 0 <= x <= self.x_limit_reservoir and 0 <= y <= self.y_limit_reservoir:
            p = self.matrix_rotation(self.reservoir_rotation).dot(np.array((x, y)))
            # robot.DMoveJoints(*self.safe_reservoir_joints)
            safe_res_pose = [self.safe_reservoir_corner[0] + p[0], self.safe_reservoir_corner[1] + p[1],
                             self.safe_reservoir_corner[2], self.safe_reservoir_corner[3], self.safe_reservoir_corner[4],
                             self.safe_reservoir_corner[5]]
            res_pose = copy(safe_res_pose)
            res_pose[2] -= 20  # in xyzabc
            self.move_to_home()
            self.driver_robot.DMoveJoints(
                *self.safe_reservoir_joints)  # we will not hit anything between home and the safe sample corner
            self.driver_robot.DMovePose(*safe_res_pose)  # don't want to hit anything
            self.driver_robot.DQLinZ(z=-20)  # need to go straight down
        else:
            raise Exception('you are out of boundary')

    def moveup(self,z=50):
        pos = list(self.driver_robot.DGetPose())
        pos[2] += z
        self.driver_robot.DMovePose(*pos)

    def removedrop(self,y=-20):
        pos = list(self.driver_robot.DGetPose())
        pos[1] += y
        self.driver_robot.DMovePose(*pos)
        self.move_to_home()

    def mv2waste(self, x, y):
        if 0 <= x <= self.x_limit_waste and 0 <= y <= self.y_limit_waste:
            p = self.matrix_rotation(self.waste_rotation).dot(np.array((x, y)))
            # robot.DMoveJoints(*self.safe_waste_joints)
            safe_waste_pose = [self.safe_waste_corner[0] + p[0], self.safe_waste_corner[1] + p[1],
                               self.safe_waste_corner[2],
                               self.safe_waste_corner[3], self.safe_waste_corner[4], self.safe_waste_corner[5]]
            waste_pose = copy(safe_waste_pose)
            waste_pose[2] -= 20
            plate_waste_pose = safe_waste_pose  # in xyzabc
            self.move_to_home()
            self.driver_robot.DMoveJoints(
                *self.safe_waste_joints)  # we will not hit anything between home and the safe sample corner
            self.driver_robot.DMovePose(*safe_waste_pose)  # don't want to hit anything
            self.driver_robot.DQLinZ(z=-20)  # need to go straight down
        else:
            raise Exception('you are out of boundary')

    # move gripper to a specified position, at speed and with defined force @helge
    def mvgripper(self, position, speed, force, robot):
        pass

    # just open the gripper @helge
    def open(self):
        pass

    # move the linear rail to a certain position @helge
    def mvrailabs(self, pos):
        pass

    # move the linear rail to a relative position @helge
    def mvrailrel(self, dist):
        pass

    def disconnect(self):
        self.driver_robot.disconnect()
