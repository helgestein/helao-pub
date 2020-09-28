# action_server for mecademic @fuzhan
# implement common movement procedures
import sys
sys.path.append(r'../driver')
sys.path.append(r'../config')
sys.path.append(r'../server')
from mischbares_small import config
#import mecademic_server
from copy import copy
import numpy as np
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests


# Add limit rejection
# Add orientationhelp so we can load the same platemap for every plane and it takes care of it

app = FastAPI(title="Mecademic action server V1", 
    description="This is a fancy mecademic action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters :dict = None
    data: dict = None

@app.get("/movement/matrixRotation")
def matrix_rotation(theta: float):
    theta = np.radians(theta)
    c, s = np.cos(theta), np.sin(theta)
    R = np.array(((c, -s), (s, c)))   
    data = requests.get("{}/movement/rotation".format(url), params={"theta": theta}).json()
    
    retc = return_class(measurement_type='movement_command', parameters= {'command':'getmatrixrotation', "rotation_value": theta}, 
                        data = {'data': data})
    return retc, R


@app.get("/movement/moveToHome")
def move_to_home():
    # this moves the robot safely to home which is defined as all joints are at 0
    paramd = {lett:val for lett,val in zip("abcdef",zeroj)}
    requests.get("{}/mecademic/dMoveJoints".format(url), params=paramd).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'move_to_home'})
    return retc

@app.get("/movement/jogging")
def jogging(joints):
    paramd = {lett: val for lett,val in zip("abcdef", joints)}
    requests.get("{}/mecademic/dMoveJoints".format(url), params= paramd).json()
    print('Please jog the robot. \n dist:axis \n (i.e 0.1:x, 0.1:y or 0.1:z dist in mm)')
    print('this runs until you say exit')
    pose = copy(requests.get("{}/mecademic/dGetPose".format(url)).json()['data']['poses'])
    pjoint = copy(requests.get("{}/mecademic/dGetJoints".format(url)).json()['data']['joints'])
    while True:
        inp = input()
        if inp == 'exit':
            pose = requests.get("{}/mecademic/dGetPose".format(url)).json()['data']['poses']
            pjoint = requests.get("{}/mecademic/dGetJoints".format(url)).json()
            break
        print(inp)
        dist, axis = inp.split(':')
        # Ask the robot to move the poses by distance in axis direction
        dist = float(dist)
        if axis == 'x':
            pose_mod = copy(list(pose))
            pose_mod[0] += dist
            paramd = {lett: val for lett,val in zip("abcdef", pose_mod)}
            requests.get("{}/mecademic/dMovePose".format(url), params= paramd).json()
    
        if axis == 'y':
            pose_mod = copy(list(pose))
            pose_mod[1] += dist
            paramd = {lett: val for lett,val in zip("abcdef", pose_mod)}
            requests.get("{}/mecademic/dMovePose".format(url), params= paramd).json()
        
        if axis == 'z':
            pose_mod = copy(list(pose))
            pose_mod[2] += dist
            paramd = {lett: val for lett,val in zip("abcdef", pose_mod)}
            requests.get("{}/mecademic/dMovePose".format(url), params= paramd).json()

        pose = requests.get("{}/mecademic/dGetPose".format(url)).json()['data']['poses']
        pjoint = requests.get("{}/mecademic/dGetJoints".format(url)).json()

    # move to the safe plane and then return the values
    pose_mod = copy(list(pose))
    pose_mod[2] += 20
    paramd = {lett: val for lett,val in zip("abcdef", pose_mod)}
    requests.get("{}/mecademic/dMovePose".format(url), params= paramd).json()
    pose = requests.get("{}/mecademic/dGetPose".format(url)).json()
    pjoint = requests.get("{}/mecademic/dGetJoints".format(url)).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'jogging', 'poses': pose, 'joints': pjoint})
    return retc, pose, pjoint

# Alignment to sample corner
@app.get("/movement/alignSample")
def align_sample():
    data, safe_sample_corner, safe_sample_joint = jogging(safe_sample_joints)
    retc = return_class(measurement_type='movement_command', parameters= {'command':'align_sample'}, 
    data = {'data': data})
    safe_points['safe_sample_corner'] = safe_sample_corner['data']['poses'] 
    safe_points['safe_sample_joint'] = safe_sample_joint['data']['joints']
    print(safe_sample_corner)
    print(safe_points)
    return retc, safe_points['safe_sample_corner'], safe_points['safe_sample_joint']

# Alignment to reservoir corner
@app.get("/movement/alignReservoir")
def align_reservoir():
    data, safe_reservoir_corner, safe_reservoir_joint = jogging(safe_reservoir_joints)
    retc = return_class(measurement_type='movement_command', parameters= {'command':'align_reservoir'}, 
    data = {'data': data})
    safe_points['safe_reservoir_corner'] = safe_reservoir_corner['data']['poses']
    safe_points['safe_reservoir_joint'] = safe_reservoir_joint['data']['joints']
    return retc, safe_points['safe_reservoir_corner'] , safe_points['safe_reservoir_joint']

# Alignment to waste corner 
@app.get("/movement/alignWaste")
def align_waste():
    data, safe_waste_corner, safe_waste_joint = jogging(safe_waste_joints)
    retc = return_class(measurement_type='movement_command', parameters= {'command':'align_waste'}, 
    data = {'data': data})
    safe_points['safe_waste_corner'] = safe_waste_corner['data']['poses']
    safe_points['safe_waste_joint'] = safe_waste_joint['data']['joints']
    
    return retc, safe_points['safe_waste_corner'] , safe_points['safe_waste_joint']

@app.get("/movement/alignment")
def alignment():
    print(safe_points)
    move_to_home()
    print('Sample Alignment...')
    align_sample()
    move_to_home()
    print('Reservoir Alignment...')
    align_reservoir()
    move_to_home()
    print('Waste Alignment...')
    align_waste()
    move_to_home()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'alignment'})
    print(safe_points)
    return retc

@app.get("/movement/mvToSample")
def mv2sample(x: float, y:float):
    if 0 <= x <= x_limit_sample and 0 <= y <= y_limit_sample:
        data, R = matrix_rotation(sample_rotation)
        p = np.dot(R, np.array((x,y)))
        safe_sample_pose = [safe_points['safe_sample_corner'][0] + p[0], safe_points['safe_sample_corner'][1] + p[1],
                            safe_points['safe_sample_corner'][2],
                            safe_points['safe_sample_corner'][3], safe_points['safe_sample_corner'][4], 
                            safe_points['safe_sample_corner'][5]]
        sample_pose = copy(safe_sample_pose)
        sample_pose[2] -= 20
        move_to_home()
        # avoid from hitting anything between home and safe sample corner
        paramd = {lett: val for lett,val in zip("abcdef", safe_points['safe_sample_joint'])}
        requests.get("{}/mecademic/dMoveJoints".format(url), params= paramd).json()
        # avoid from hitting anything
        paramP = {lett: val for lett,val in zip("abcdef", safe_sample_pose)}
        requests.get("{}/mecademic/dMovePose".format(url), params= paramP).json()
        # going straight down
        requests.get("{}/mecademic/dqLinZ".format(url), params= {'z': -20, 'nsteps':100} ).json()  
    else:
        raise Exception('you are out of boundary')

    retc = return_class(measurement_type='movement_command', parameters= {'command':'mv2sample', 'x': x, 'y': y})
    return retc

@app.get("/movement/mvToReservoir")
def mv2reservoir(x: float, y: float):
    if 0 <= x <= x_limit_reservoir and 0 <= y <= y_limit_reservoir:
        data, R = matrix_rotation(reservoir_rotation)
        p = np.dot(R, np.array((x,y)))
        #p = matrix_rotation(reservoir_rotation).dot(np.array((x, y)))
        safe_res_pose = [safe_points['safe_reservoir_corner'][0] + p[0], safe_points['safe_reservoir_corner'][1] + p[1],
                            safe_points['safe_reservoir_corner'][2], safe_points['safe_reservoir_corner'][3], 
                            safe_points['safe_reservoir_corner'][4], safe_points['safe_reservoir_corner'][5]]
        res_pose = copy(safe_res_pose)
        res_pose[2] -= 20  # in xyzabc
        move_to_home()
        #avoid from hitting anything between home and safe reservoir corner
        paramd = {lett: val for lett,val in zip("abcdef", safe_points['safe_reservoir_joint'])}
        requests.get("{}/mecademic/dMoveJoints".format(url), params= paramd).json()
        # avoid from hitting anything
        paramP = {lett: val for lett,val in zip("abcdef", safe_res_pose)}
        requests.get("{}/mecademic/dMovePose".format(url), params= paramP).json()
        # going straight down
        requests.get("{}/mecademic/dqLinZ".format(url), params= {'z': -20, 'nsteps':100} ).json()
    else:
        raise Exception('you are out of boundary')
    
    retc = return_class(measurement_type='movement_command', parameters= {'command':'mv2reservoir', 'x': x, 'y': y})
    return retc

   
@app.get("/movement/mvToWaste")    
def mv2waste(x: float, y: float):
    if 0 <= x <= x_limit_waste and 0 <= y <= y_limit_waste:
        data, R= matrix_rotation(waste_rotation)
        p = np.dot(R, np.array((x,y)))
        # p = matrix_rotation(waste_rotation).np.dot(np.array((x, y)))
        # robot.DMoveJoints(*self.safe_waste_joints)
        safe_waste_pose = [safe_points['safe_waste_corner'][0] + p[0], 
                            safe_points['safe_waste_corner'][1] + p[1], safe_points['safe_waste_corner'][2],
                            safe_points['safe_waste_corner'][3], safe_points['safe_waste_corner'][4], 
                            safe_points['safe_waste_corner'][5]]
        
        waste_pose = copy(safe_waste_pose)
        waste_pose[2] -= 20
        plate_waste_pose = safe_waste_pose  # in xyzabc
        move_to_home()
        # avoid from hitting anything between safe waste corner and home 
        paramd = {lett: val for lett,val in zip("abcdef", safe_points['safe_waste_joint'])}
        datad = requests.get("{}/mecademic/dMoveJoints".format(url), params= paramd).json()
        # avoid from hitting anything
        paramP = {lett: val for lett,val in zip("abcdef", safe_waste_pose)}
        datap = requests.get("{}/mecademic/dMovePose".format(url), params= paramP).json()
        # going straight down
        dataz = requests.get("{}/mecademic/dqLinZ".format(url), params= {'z': -20, 'nsteps':100} ).json()
    
    else:
        raise Exception('you are out of boundary')
       
    retc = return_class(measurement_type='movement_command', parameters= {'command':'mv2waste', 'x': x, 'y': y}, 
                        data= {'joints': datad, 'poses': datap, 'z': dataz})
    return retc
 

@app.get("/movement/moveUp")
def moveup(z: float=50.0):
    pos = requests.get("{}/mecademic/dGetPose".format(url)).json()["data"]["poses"]
    pos[2] += z
    paramd = {lett: val for lett,val in zip("abcdef", pos)}
    data = requests.get("{}/mecademic/dMovePose".format(url), params= paramd).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'moveup', 'z': z}, data = {'data': data})
    return retc
    
@app.get("/movement/removeDrop")
def removedrop(y: float=-20):
    pos = list(requests.get("{}/mecademic/dGetPose".format(url)).json()["data"]["poses"])
    pos[1] += y
    paramd = {lett: val for lett, val in zip("abcdef", pos)}
    data = requests.get("{}/mecademic/dMovePose".format(url), params= paramd).json()
    move_to_home()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'removedrop', 'y': y}, data = {'data': data})
    return retc
 
# move gripper to a specified position, at speed and with defined force @helge
def mvgripper(position, speed, force, robot):
    pass

# just open the gripper 
def open():
    pass

# move the linear rail to a certain position 
def mvrailabs(pos):
    pass

# move the linear rail to a relative position 
def mvrailrel(dist):
    pass

@app.get("/movement/bringRaman")
def bring_raman():
    data = requests.get("{}/mecademic/dMoveJoints".format(url), params={"a":-89.9997,"b":36.4794,"c":-31.4562,"d":0.0,"e":58.4774,"f":120.0028}).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'bring_raman'}, data = {'data': data})
    return retc


if __name__ == "__main__":

    url = "http://{}:{}".format(config['servers']['mecademicServer']['host'], config['servers']['mecademicServer']['port'])
    zeroj = [0, 0, 0, 0, 0, 0]
    #move_to_home()
    #these point wil be added after the alignements 
    safe_points = {'safe_sample_corner': None , 'safe_sample_joint': None, 
                    'safe_reservoir_corner': [0,0,0,0,0,0], 'safe_reservoir_joint': [0,0,0,0,0,0],
                    'safe_waste_corner': [0,0,0,0,0,0], 'safe_waste_joint': [0,0,0,0,0,0]}

    safe_sample_joints = config['movement']['safe_sample_joints']
    safe_reservoir_joints = config['movement']['safe_reservoir_joints']
    safe_waste_joints = config['movement']['safe_waste_joints']
    sample_rotation = config['movement']['sample_rotation']
    reservoir_rotation = config['movement']['reservoir_rotation']
    waste_rotation = config['movement']['waste_rotation']
    x_limit_sample = config['movement']['x_limit_sample']
    y_limit_sample = config['movement']['y_limit_sample']
    x_limit_reservoir = config['movement']['x_limit_reservoir']
    y_limit_reservoir = config['movement']['y_limit_reservoir']
    x_limit_waste = config['movement']['x_limit_waste']
    y_limit_waste = config['movement']['y_limit_waste']


    
    uvicorn.run(app, host=config['servers']['movementServer']['host'], port=config['servers']['movementServer']['port'])
    print("instantiated mecademic")
    