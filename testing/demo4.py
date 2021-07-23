import requests
import json
import numpy as np
import random
import sys
sys.path.append(r'../config')
sys.path.append('config')
from sdc_1 import config


def test_fnc(sequence,thread=0):
    server = 'orchestrator'
    action = 'addExperiment'
    params = dict(experiment=json.dumps(sequence),thread=thread)
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
    return result
# real run
substrate = 53
x, y = np.meshgrid([2.5 * i for i in range(20)],[2.5 * i for i in range(20)])
x, y = x.flatten(), y.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
first_arbitary_choice = random.choice(x_query)
dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
y_query = [schwefel_function(x[0], x[1])for x in x_query]
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query})  
dz = config['lang']['safe_sample_pos'][2]

n = 5
test_fnc(dict(soe=['orchestrator/start','lang/moveWaste_0', 'pump/formulation_0', 'lang/RemoveDroplet_0',
                   'lang/moveSample_0','lang/moveAbs_0','lang/moveDown_0', 'autolab/measure_0',
                   'measure/schwefelFunction_0','analysis/dummy_0'], 
            params={'start': {'collectionkey' : 'demo4'},
                    'moveWaste_0':{'x': 0, 'y':0, 'z':0},
                    'formulation_0': {'speed': 70, 'volume': 50, 'direction':1},
                    'RemoveDroplet_0': {'x':0, 'y':0, 'z':0},
                    'moveSample_0': {'x':0, 'y':0, 'z':0},
                    'moveAbs_0': {'dx':dx0, 'dy':dy0, 'dz':dz}, 
                    'moveDown_0': {'dz'=0.12, 'steps':4, 'maxForce':1.4, 'threshold': 0.13},
                    'measure_0': {'procedure': 'ca', 'setpointjson': json.dumps({'applypotential': {'Setpoint value': -0.3},
                                                'recordsignal': {'Duration': 15}}),
                                                'plot':'tCV',
                                                'onoffafter':'off',
                                                'safepath':'C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp',
                                                'filename':'substrate_{}_ca_0_15.nox'.format(substrate),
                                                'parseinstructions':'recordsignal'},
                    'schwefelFunction_0':{'x':dx0,'y':dy0},
                    'dummy_0':{'x_address':'experiment_0:0/schwefelFunction_0/data/parameters/x',
                                'y_address':'experiment_0:0/schwefelFunction_0/data/parameters/y',
                                'schwefel_address':'experiment_0:0/schwefelFunction_0/data/data/key_y'}}, 
            meta=dict()))

for i in range(n):
    test_fnc(dict(soe=[f'ml/activeLearning_{i}',f'orchestrator/modify_{i}',f'lang/moveWaste_{i+1}', f'pump/formulation_{i+1}', f'lang/RemoveDroplet_{i+1}',
                       f'lang/moveSample_{i+1}',f'lang/moveAbs_{i+1}',f'lang/moveDown_{i+1}', f'autolab/measure_{i+1}',
                       f'measure/schwefelFunction_{i+1}',f'analysis/dummy_{i+1}'], 
                  params={f'activeLearning_{i}':{'query':query,'address':f'experiment_{i}:0/dummy_{i}/data/data'},
                            f'modify_{i}': {'addresses':[f'experiment_{i+1}:0/activeLearning_{i}/data/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearning_{i}/data/data/next_y',
                                                         f'experiment_{i+1}:0/activeLearning_{i}/data/data/next_x',
                                                         f'experiment_{i+1}:0/activeLearning_{i}/data/data/next_y'],
                                            'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y',
                                                        f'moveAbs_{i+1}/dx', f'moveAbs_{i+1}/dy']},
                            f'moveWaste_{i+1}':{'x': 0, 'y':0, 'z':0},
                            f'formulation_{i+1}': {'speed': 70, 'volume': 50, 'direction':1},
                            f'RemoveDroplet_{i+1}': {'x':0, 'y':0, 'z':0},
                            f'moveSample_{i+1}': {'x':0, 'y':0, 'z':0},
                            f'moveAbs_{i+1}': {'dx':'?', 'dy':'?', 'dz':dz}, 
                            f'moveDown_{i+1}': {'dz'=0.12, 'steps':4, 'maxForce':1.4, 'threshold': 0.13},
                            f'measure_{i+1}': {'procedure': 'ca', 'setpointjson': json.dumps({'applypotential': {'Setpoint value': -0.3},
                                                'recordsignal': {'Duration': 15}}),
                                                'plot':'tCV',
                                                'onoffafter':'off',
                                                'safepath':'C:/Users/LaborRatte23-3/Documents/GitHub/helao-dev/temp',
                                                'filename':'substrate_{}_ca_0_15.nox'.format(substrate),
                                                'parseinstructions':'recordsignal'},
                            f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                            f'dummy_{i+1}':{'x_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/x',
                                            'y_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/y',
                                            'schwefel_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/data/key_y'}}, 
                  meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))