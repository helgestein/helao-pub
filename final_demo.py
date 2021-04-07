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


# real run
x, y = np.meshgrid([0.25 * i for i in range(20)],
                   [0.25 * i for i in range(20)])
x, y = x.flatten(), y.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
x_query = str(x_query)
dz = config['lang']['safe_sample_pos'][2]

# need to specify the session name

substrate = 30
# in the first move we just choose one arbitary point


test_fnc(dict(soe=['orchestrator/start'], params={'start': None}, meta=dict(substrate=substrate, ma=[
         config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=0.005)))

run_sequence = dict(soe=['measure/schwefelFunction_0', 'analysis/dummy_0'],
                    params=dict(schwefelFunction_0=dict(
                        measurement_area=str([{}, {}]).format(dx0, dy0), save_data_to="C:/Users/Fuzhi/Documents/GitHub/helao_dev/data/schwefel_fnc_{}.json".format(0)),
    dummy_0=dict(exp_num='measurement_no_0', sources='session')),  # key_y should be the output of the schwefel function
    meta=dict(substrate=substrate, ma=[round(dx0 * 100)*10, round(dy0 * 100)*10],  r=0.005))
test_fnc(run_sequence)

for j in range(1, 400, 1):
    # according to the output of the active learning, we need to feed the nexr pos to motor
    exp_num = 'measurement_no_{}'.format(j)
    print(exp_num)
    run_sequence = dict(soe=['learning/activeLearning_0', 'measure/schwefelFunction_0', 'analysis/dummy_0', ],
                        params=dict(activeLearning_0=dict(session='session', x_query=x_query, save_data_path='C:/Users/Fuzhi/Documents/GitHub/helao_dev/ml_data/ml_analysis_{}.json'.format(exp_num), addresses=json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"]), pointers=json.dumps(['moveAbs_0/dx', 'moveAbs_0/dy', 'schwefel_function_0/measurement_area'])),
                                    schwefelFunction_0=dict(
                                        measurement_area='?', save_data_to="C:/Users/Fuzhi/Documents/GitHub/helao_dev/data/schwefel_fnc_{}.json".format(exp_num)),
                                    dummy_0=dict(exp_num=exp_num, sources='session')),  # key_y should be the output of the schwefel function)
                        meta=dict(substrate=substrate, ma=[round(2 * 100)*10, round(2 * 100)*10],  r=0.005))

    test_fnc(run_sequence)


test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta=dict(substrate=substrate, ma=[
         config['lang']['safe_sample_pos'][0], config['lang']['safe_sample_pos'][1]], r=0.005)))
