import requests
from copy import copy
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
sys.path.append(r'../orchestrators')

import time
from config.mischbares_small import config
import json
from copy import copy
import os

import numpy as np
import matplotlib.pyplot as plt


def test_fnc(sequence):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence))
    requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()

# real run 
x, y = np.meshgrid([2.5 * i for i in range(18)], [2.5 * i for i in range(12)])
x, y = x.flatten(), y.flatten()
pot = np.linspace(0, 2, num=72)
cur = np.linspace(-0.01, 0.01, num= 72)
uppervort = [x+0.5 for x in pot]
lowervort = [x-0.5 for x in pot]


# pot[j]
all_seq = []
for j in range(216):

    print("{}, {}".format(x[j], y[j]))
    dx = config['lang']['safe_sample_pos'][0] + x[j]
    dy = config['lang']['safe_sample_pos'][1] + y[j]
    dz = config['lang']['safe_sample_pos'][2]

    if j < 72:
        run_sequence= dict(soe=['motor/moveWaste_0', 'pumping/formulation_0', 'motor/RemoveDroplet_0', 'motor/moveAbs_0','motor/moveSample_0', 
                            'motor/moveAbs_1','motor/moveDown_0',
                            'echem/measure_0', 'pumping/formulation_1', 'motor/moveRel_0', 'motor/moveWaste_1'],
                            params= dict(moveWaste_0= None,  
                            formulation_0= dict(comprel='[0.125]', pumps= '[0]',speed= 400, totalvol=50, direction=1), 
                            RemoveDroplet_0= None, 
                            moveAbs_0 = dict(dx=9.5, dy=13.0, dz=2.0),
                            moveSample_0= None, 
                            moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                            moveDown_0 = dict(dz=0.493, steps=40, maxForce=0.04, threshold= 0.5),
                            measure_0= dict(procedure="cp", setpointjson= json.dumps({'applycurrent': {'Setpoint value': cur[j]}, 'recordsignal': {'Duration': 120}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                filename="cp_{}.nox".format(j),
                                parseinstructions='recordsignal'), 
                            formulation_1= dict(comprel='[0.125]', pumps= '[0]',speed= 150, totalvol=10, direction=0),
                            moveRel_0= dict(dx=0, dy=0, dz=-20), 
                            moveWaste_1= None),
                        meta=dict(ma=1 , substrate=j))

    elif 71 < j < 144:
        run_sequence= dict(soe=['motor/moveWaste_0', 'pumping/formulation_0', 'motor/RemoveDroplet_0', 'motor/moveAbs_0','motor/moveSample_0', 
                            'motor/moveAbs_1','motor/moveDown_0',
                            'echem/measure_0', 'pumping/formulation_1', 'motor/moveRel_0', 'motor/moveWaste_1'],
                            params= dict(moveWaste_0= None,  
                            formulation_0= dict(comprel='[0.125]', pumps= '[0]',speed= 400, totalvol=50, direction=1), 
                            RemoveDroplet_0= None, 
                            moveAbs_0 = dict(dx=9.5, dy=13.0, dz=2.0),
                            moveSample_0= None, 
                            moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                            moveDown_0 = dict(dz=0.493, steps=40, maxForce=0.04, threshold= 0.5),
                            measure_0= dict(procedure="ca", setpointjson= json.dumps({'applypotential': {'Setpoint value': pot[j%72]}, 'recordsignal': {'Duration': 120}}),
                                        plot="tCV",
                                        onoffafter="off",
                                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                        filename="ca_{}.nox".format(j%72),
                                        parseinstructions='recordsignal'), 
                            formulation_1= dict(comprel='[0.125]', pumps= '[0]',speed= 150, totalvol=10, direction=0),
                            moveRel_0= dict(dx=0, dy=0, dz=-20),
                            moveWaste_1= None),
                            meta=dict(ma=1 , substrate=j))
        
    else:
        run_sequence= dict(soe=['motor/moveWaste_0', 'pumping/formulation_0', 'motor/RemoveDroplet_0', 'motor/moveAbs_0','motor/moveSample_0', 
                            'motor/moveAbs_1','motor/moveDown_0',
                            'echem/measure_0', 'pumping/formulation_1', 'motor/moveRel_0','motor/moveWaste_1'],
                            params= dict(moveWaste_0= None,  
                            formulation_0= dict(comprel='[0.125]',
                            pumps= '[0]',speed= 400, totalvol=50, direction=1), RemoveDroplet_0= None, 
                            moveAbs_0 = dict(dx=9.5, dy=13.0, dz=2.0),
                            moveSample_0= None, 
                            moveAbs_1 = dict(dx=dx, dy=dy, dz=dz),
                            moveDown_0 = dict(dz=0.493, steps=40, maxForce=0.04, threshold= 0.5),
                            measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': pot[j%72]}, 'FHWait': {'Time': 10}, 
                                        'CVLinearScanAdc164': {'StartValue': pot[j%72], 'UpperVertex': uppervort[j%72], 'LowerVertex':lowervort[j%72], 'NumberOfStopCrossings': 6, 'ScanRate': 0.1}}),
                                        plot="tCV",
                                        onoffafter="off",
                                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                        filename="cv_{}.nox".format(j),
                                        parseinstructions='CVLinearScanAdc164'), 
                            formulation_1= dict(comprel='[0.125]', pumps= '[0]',speed= 150, totalvol=10, direction=0),
                            moveRel_0= dict(dx=0, dy=0, dz=-20),
                            moveWaste_1= None),
                            meta=dict(ma=1 , substrate=j))

    add_collection = ["data/addCollection_0"]
    add_collection_params = dict(addCollection_0= dict(identifier="test_demo", title="checkup"))
    i = 0
    for filename in os.listdir(r"C:\Users\Fuzhi\Documents\GitHub\helao-dev\temp"):
        ident = filename.split("_")[0]
        add_collection.append("data/makeRecordFromFile_{}".format(i))
        add_collection_params.update({"makeRecordFromFile_{}".format(i): dict(filename= filename, filepath=r"C:\Users\Fuzhi\Documents\GitHub\helao-dev\temp")})
        add_collection.append("data/addRecordToCollection_{}".format(i))
        add_collection_params.update({"addRecordToCollection_{}".format(i): dict(identCollection= "electrodeposition data", identRecord=ident)})
        i += 1
        run_sequence['soe'] += add_collection
        run_sequence['params'].update(add_collection_params)

    # all_seq.append(copy(run_sequence))
    test_fnc(run_sequence)

###############################
#start the infinite loop
server = 'orchestrator'
action = 'infiniteLoop'
params = None
requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()


########################
#emergency stop
server = 'orchestrator'
action = 'emergencyStop'
params = None
requests.post("http://{}:{}/{}/{}".format(
    config['servers']['orchestrator']['host'] ,13380 ,server ,action),
    params= params).json()



#################################################################
# #sequesnce of the lang_motor action
lang_sequence= dict(soe=['motor/getPos_0', 'motor/moveRel_0', 'motor/moveAbs_0',
                         'motor/moveHome_0','motor/moveWaste_0', 'motor/getPos_1', 'motor/moveDown_0'], 
                    params= dict(getPos_0 = None, moveRel_0= dict(dx=-10, dy=-10, dz=50),
                                moveAbs_0= dict(dx=0, dy=0, dz=0), moveHome_0= None,
                                moveWaste_0= None, getPos_1= None, moveDown_0= dict(dz=1, steps=10, maxForce=0.1)),
                    meta=dict(ma=1 , substrate=1))

test_fnc(lang_sequence)

lang_sequence= dict(soe=['motor/moveDown_0'], 
                    params= dict(moveDown_0= dict(dz=10,steps=5,maxForce=0.1)),
                    meta=dict(ma=1 , substrate=1))
test_fnc(lang_sequence)



#################
# #sequence of echem functions 
echem_sequence = dict(soe= ['echem/potential_0', 'echem/ismeasuring_0',
                            'echem/current_0', 'echem/appliedpotential_0', 'echem/setCurrentRange_0',
                            'echem/cellonoff_0', 'echem/measure_0'],
                    params= dict(potential_0 = None, ismeasuring_0= None, current_0= None,
                             appliedpotential_0= None, setCurrentRange_0= dict(crange='10mA'),
                             cellonoff_0= dict(onoff='off'), measure_0= dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal")),
                    meta=dict(ma=1 , substrate=1))

test_fnc(echem_sequence)

#################
# #sequence of echem functions 
#cp test
echem_sequence = dict(soe= ['echem/measure_0'],
                    params= dict(measure_0= dict(procedure="cp", setpointjson= json.dumps({'applycurrent': {'Setpoint value': 0.12738}, 'recordsignal': {'Duration': 50}}),
                                plot="tCV",
                                onoffafter="off",
                                safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                filename="cp.nox",
                                parseinstructions='recordsignal')),
                    meta=dict(ma=1 , substrate=1))

test_fnc(echem_sequence)

#cv test
echem_sequence = dict(soe= ['echem/measure_0'],
                    params= dict(measure_0= dict(procedure="cv", setpointjson= json.dumps({'FHSetSetpointPotential': {'Setpoint value': 0}, 'FHWait': {'Time': 10}, 
                                        'CVLinearScanAdc164': {'StartValue': 0, 'UpperVertex': 1, 'LowerVertex':-1, 'NumberOfStopCrossings': 6, 'ScanRate': 0.1}}),
                                        plot="tCV",
                                        onoffafter="off",
                                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                                        filename="cv.nox",
                                        parseinstructions='CVLinearScanAdc164')),
                    meta=dict(ma=1 , substrate=1))

test_fnc(echem_sequence)

##################sequence of force
force_sequence = dict(soe= ['forceAction/read_0'],
                      params= dict(read_0= None),
                      meta=dict(ma=1 , substrate=1))

test_fnc(force_sequence)

############# sequence of pump
pump_sequence = dict(soe= ['pumping/formulation_0', 'pumping/flushSerial_0','pumping/resetPrimings_0', 
                            'pumping/getPrimings_0','pumping/refreshPrimings_0'],
                      params= dict(formulation_0= dict(comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
                                                        pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',speed= 8000, totalvol=2000),
                                    flushSerial_0=None, resetPrimings_0= None, getPrimings_0= None, refreshPrimings_0=None),
                      meta= dict(ma=2 , substrate=1))

test_fnc(pump_sequence)

##########################
#test all instruments at once
dry_run_sequence_1= dict(soe=['motor/moveHome_0', 'motor/getPos_0', 'motor/moveAbs_0', 
                    'pumping/formulation_0', 'forceAction/read_0', 'motor/getPos_1',
                    'motor/moveDown_0', 'echem/measure_0', 'motor/moveWaste_0', 'motor/moveHome_1'],
                    params= dict(moveHome_0= None, getPos_0= None, moveAbs_0= dict(dx=65, dy=85, dz=5), 
                    formulation_0= dict(comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
                    pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',speed= 8000, totalvol=2000), read_0= None, 
                    getPos_1= None, moveDown_0= dict(dz=1, steps=10, maxForce=0.1), 
                    measure_0= dict(procedure="ca", setpointjson="{'applypotential': {'Setpoint value': 0.01}, 'recordsignal': {'Duration': 10}}",
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal"), moveWaste_0= None, moveHome_1= None),
                meta=dict(ma=1 , substrate=1))
dry_run_sequence_2= dict(soe=['motor/moveHome_0', 'motor/getPos_0', 'motor/moveAbs_0', 
                    'pumping/formulation_0', 'forceAction/read_0', 'motor/getPos_1',
                    'motor/moveDown_0', 'echem/measure_0', 'motor/moveWaste_0', 'motor/moveHome_1'],
                    params= dict(moveHome_0= None, getPos_0= None, moveAbs_0= dict(dx=70, dy=80, dz=4), 
                    formulation_0= dict(comprel='[0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125]',
                    pumps= '[0, 1, 2, 4, 6, 7, 10, 12]',speed= 8000, totalvol=2000), read_0= None, 
                    getPos_1= None, moveDown_0= dict(dz=2, steps=20, maxForce=0.1), 
                    measure_0= dict(procedure="ca", setpointjson= json.dumps({'applypotential': {'Setpoint value': pot[j]}, 'recordsignal': {'Duration': 10}}),
                        plot="tCV",
                        onoffafter="off",
                        safepath="C:/Users/SDC_1/Documents/deploy/helao-dev/temp",
                        filename="ca.nox",
                        parseinstructions="recordsignal"), moveWaste_0= None, moveHome_1= None),
                meta=dict(ma=1 , substrate=2))

test_fnc(dry_run_sequence_1)
test_fnc(dry_run_sequence_2)
################################