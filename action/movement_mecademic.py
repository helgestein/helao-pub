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
import time

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
    paramd = {lett:val for lett,val in zip("abcdef",config['movement']['zeroj'])}
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

@app.get("/movement/safeRaman")
def safe_raman():
    #probe height calibrated using stainless steel PIKEM coin cell spacer of .5mm thickness. 
    #probe is placed in current printed holder with groove in probe head just above front edge of holder.
    #probe is not perfectly perpendicular to surface, and discrepancy of probe height between sides is something on the order of 10th's of millimeters
    #some slight effort was made to choose a height at which the spacer could fit under the edge of the probe at about 180° of the cylinder, but this is very inexact
    #these are the joints then, at which we assume the raman probe is .5mm above sample in current calibration: [-89.9993, 31.1584, -1.9319, 0.0, 34.2737, 120.0039]
    #thus, in these joints we assume we are 20mm above sample table: [-89.9993, 29.9845, -9.0722, 0.0, 42.5878, 120.0038]
    data = requests.get("{}/mecademic/dMoveJoints".format(url), params={"a":-89.9993,"b":29.9845,"c":-9.0722,"d":0.0,"e":42.5878,"f":120.0038}).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'safe_raman'}, data = {'data': data})
    return retc

@app.get("/movement/measuringRaman")
def measuring_raman(z:float,h:float):
    #h is substrate thickness
    #z is height above substrate to measure at
    #first check if in safe position
    safe_raman()
    #math here assumes you are 20mm above table, and want to move to 5mm above sample for optimal raman measurement
    data = requests.get("{}/mecademic/dqLinZ".format(url), params={"z":z+h-20}).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'measuring_raman','parameters':{'h':h,'z':z}}, data = {'data': data})
    return retc

@app.get("/movement/calibrateRaman")
def calibrate_raman(zs:str,h:float,t:int,safepath:str):
    #h is substrate thickness
    #t is integration time in µs
    data,best = [],{}
    #test integral of spectrum at this list of heights above substrate, to figure out where you get best signal
    zs = json.loads(zs)
    safe_raman()
    zc = 20-h
    for z in zs:
        zcall = requests.get("{}/mecademic/dqLinZ".format(url), params={"z":z-zc}).json()
        rcall = requests.get("http://{}:{}/ocean/readSpectrum".format(config['servers']['oceanServer']['host'], config['servers']['oceanServer']['port']),params={'t':t,'filename':safepath+"/raman_calibration_"+str(time.time())}).json()
        zc = z
        tot = sum(rcall['data']['intensities'])
        data.append(dict(movement=zcall,read=rcall,z=z,int=tot))
        if best == {} or tot > best['int']:
            best = dict(z=z,int=tot)
    safe_raman()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'calibrate_raman','parameters':{'h':h,'t':t}}, data = {'trials': data,'best': best})
    return retc

#used for calibration. for a given height z above substrate of thickness h, 
#move to height z and return integral over raman intensity with integration time t
@app.get("/movement/zvi")
def zvi(z:float,h:float,t:int,):
    pass


@app.get("/movement/safeFTIR")
def safe_FTIR():
    #(5.7103, 1.7055, 55.8257, 6.7592, -57.7119, -2.8806) for .5mm above stage for FTIR
    #(5.7103, -3.6963, 51.0918, 7.7078, -48.4622, -4.4683) for 20mm above stage??? something weird happened
    data = requests.get("{}/mecademic/dMoveJoints".format(url), params={"a":-89.9994,"b":30.1113,"c":-7.5789,"d":0.0,"e":40.9681,"f":120.0034}).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'bring_raman'}, data = {'data': data})
    return retc

@app.get("/movement/measuringFTIR")
def measuring_FTIR(t,d):
    #t is substrate thickness, d is probe displacement from sample
    data = requests.get("{}/mecademic/dMoveJoints".format(url), params={"a":-89.9994,"b":30.1113,"c":-7.5789,"d":0.0,"e":40.9681,"f":120.0034}).json()
    retc = return_class(measurement_type='movement_command', parameters= {'command':'bring_raman'}, data = {'data': data})
    return retc




if __name__ == "__main__":

    url = "http://{}:{}".format(config['servers']['mecademicServer']['host'], config['servers']['mecademicServer']['port'])
    zeroj = config['movement']['zeroj']
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
    