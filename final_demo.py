import itertools
import matplotlib.pyplot as plt
import numpy as np
import random
import os
import json
from config.mischbares_small import config
import time
import requests
from copy import copy

import sys
sys.path.append(r'../config')
sys.path.append(r'../driver')
sys.path.append(r'../action')
sys.path.append(r'../server')
sys.path.append(r'../orchestrators')


def test_fnc(sequence):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence))
    print("requesting")
    requests.post("http://{}:{}/{}/{}".format(
        config['servers']['orchestrator']['host'], 13380, server, action), params=params).json()


def schwefel_function(x, y):
    comp = np.array([x,y])
    sch_comp = 1000 * np.array(comp) - 500
    result = 0
    for index, element in enumerate(sch_comp):
        result += - element * np.sin(np.sqrt(np.abs(element)))
    result = (-result) / 1000
    print(result)
    return result

# real run
x, y = np.meshgrid([2.5 * i for i in range(20)],[2.5 * i for i in range(20)])
x, y = x.flatten(), y.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
x_query = json.dumps(x_query.tolist())
dz = config['lang']['safe_sample_pos'][2]

y_query = [schwefel_function(x[0], x[1])for x in x_query]
# need to specify the session name
query = {'x_query': x_query, 'y_query': y_query}

substrate = 50
# in the first move we just choose one arbitary point


test_fnc(dict(soe=['orchestrator/start'], params={'start': {'collectionkey' : 'substrate'}}, meta=dict(substrate=substrate, ma=[
         config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=0.005)))
# moveDown_0 = dict(dz=0.213, steps=120, maxForce=0.44, threshold= 0.320),
# ,'motor/moveDown_0'
run_sequence = dict(soe=['motor/moveWaste_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 
                        'motor/moveAbs_0','motor/moveDown_0'],
                        #['motor/moveWaste_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 
                        #'motor/moveAbs_0','motor/moveDown_0','measure/schwefelFunction_0', 'analysis/dummy_0']
                    params=dict(moveWaste_0= dict(x=0, y=0, z=0),  
                                RemoveDroplet_0= dict(x=0, y=0, z=0), 
                                moveSample_0= dict(x=0, y=0, z=0), 
                                moveAbs_0 = dict(dx=dx0, dy=dy0, dz=dz),
                                moveDown_0 = dict(dz=0.10, steps=1, maxForce=0.44, threshold= 0.120)),
                                schwefelFunction_0=dict(measurement_area=str([{}, {}]).format(dx0, dy0), save_data_to="C:/Users/LaborRatte23-3/Documents/schwefel_res/schwefel_fnc_{}.json".format(0)),
                                dummy_0=dict(exp_num='measurement_no_0', sources='session')), #, sources='session'  # key_y should be the output of the schwefel function
                                meta=dict(substrate=substrate, ma=[round(dx0 * 100)*10, round(dy0 * 100)*10],  r=0.005))
test_fnc(run_sequence)
#json.dumps(['moveAbs_0/dx', 'moveAbs_0/dy', 'schwefel_function_0/measurement_area'])
#addresses=json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
#,'motor/moveDown_0'
# ,'motor/moveDown_0'
for j in range(3):
    # according to the output of the active learning, we need to feed the nexr pos to motor
    # sources='session',
    exp_num = 'experiment_{}'.format(j)
    print(exp_num)
    #'learning/activeLearning_0','motor/moveWaste_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 'motor/moveAbs_0' ,'motor/moveDown_0','measure/schwefelFunction_0', 'analysis/dummy_0']
    run_sequence = dict(soe=['motor/moveWaste_0', 'motor/RemoveDroplet_0','motor/moveSample_0', 'motor/moveAbs_0' ,'motor/moveDown_0'],
                        params=dict(#activeLearning_0=dict(sources='session', x_query=x_query, save_data_path='C:/Users/LaborRatte23-3/Documents/anaylse_res/ml_analysis_{}.json'.format(exp_num), 
                        #addresses=json.dumps(["moveAbs/data/parameters/dx", "moveAbs/data/parameters/dy", "schwefelFunction/data/parameters/measurement_area","dummy/data/data/key_y"]), 
                        # #pointers=json.dumps(['moveAbs_0/dx', 'moveAbs_0/dy','schwefelFunction_0/measurement_area'])),
                                    moveWaste_0= dict(x=0, y=0, z=0),  
                                    RemoveDroplet_0= dict(x=0, y=0, z=0), 
                                    moveSample_0= dict(x=0, y=0, z=0), 
                                    moveAbs_0 = dict(dx='?', dy='?', dz=dz), 
                                    moveDown_0 = dict(dz=0.100, steps=120, maxForce=0.44, threshold= 0.120)),
                                    #schwefelFunction_0=dict(measurement_area='?', save_data_to="C:/Users/LaborRatte23-3/Documents/schwefel_res/schwefel_fnc_{}.json".format(exp_num)),
                                    #dummy_0=dict(exp_num=exp_num, sources='session')), #, sources='session'  # key_y should be the output of the schwefel function)
                                    meta=dict(substrate=substrate, ma=[round(2 * 100)*10, round(2 * 100)*10],  r=0.005))
    test_fnc(run_sequence)


test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta=dict(substrate=substrate, ma=[
         config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=0.005)))
