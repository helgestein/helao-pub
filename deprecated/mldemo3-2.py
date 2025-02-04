import requests
import json
import numpy as np
import random
import sys
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
x, y = np.meshgrid([2.5 * i for i in range(20)],[2.5 * i for i in range(20)])
x, y = x.flatten(), y.flatten()
x_query = np.array([[i, j] for i, j in zip(x, y)])
#first_arbitary_choice = random.choice(x_query)
#dx0, dy0 = first_arbitary_choice[0], first_arbitary_choice[1]
y_query = [schwefel_function(x[0], x[1])for x in x_query]
query = json.dumps({'x_query': x_query.tolist(), 'y_query': y_query})  

n = 40
test_fnc(dict(soe=['orchestrator/start','measure/schwefelFunction_0','analysis/dummy_0'], params={'start': {'collectionkey' : 'dummytest2'},'schwefelFunction_0':{'x':5,'y':10},
                   'dummy_0':{'x_address':'experiment_0:0/schwefelFunction_0/data/parameters/x','y_address':'experiment_0:0/schwefelFunction_0/data/parameters/y','schwefel_address':'experiment_0:0/schwefelFunction_0/data/data/key_y'}}, meta=dict()))
for i in range(n):
    test_fnc(dict(soe=[f'orchestrator/wait_{i}',f'orchestrator/modify_{i}',f'measure/schwefelFunction_{i+1}',f'analysis/dummy_{i+1}'], 
                params={f'wait_{i}':{'addresses':f'experiment_{i+1}:2/activeLearning_{2*i+1}'},
                        f'modify_{i}':{'addresses':[f'experiment_{i+1}:2/activeLearning_{2*i+1}/data/data/next_x',f'experiment_{i+1}:2/activeLearning_{2*i+1}/data/data/next_y'],'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y']},f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                        f'dummy_{i+1}':{'x_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/x','y_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/y','schwefel_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/data/key_y'}}, meta=dict()))

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}))



test_fnc(dict(soe=['orchestrator/wait_0','orchestrator/modify_0','measure/schwefelFunction_0','analysis/dummy_0'], params={'wait_0':{'addresses':'experiment_0:2/activeLearning_0'},
                   'modify_0':{'addresses':['experiment_0:2/activeLearning_0/data/data/next_x','experiment_0:2/activeLearning_0/data/data/next_y'],'pointers':['schwefelFunction_0/x','schwefelFunction_0/y']},
                   'schwefelFunction_0':{'x':'?','y':'?'},
                   'dummy_0':{'x_address':'experiment_0:0/schwefelFunction_0/data/parameters/x','y_address':'experiment_0:0/schwefelFunction_0/data/parameters/y','schwefel_address':'experiment_0:0/schwefelFunction_0/data/data/key_y'}}, meta=dict()),1)

for i in range(n):
    test_fnc(dict(soe=[f'orchestrator/wait_{i+1}',f'orchestrator/modify_{i+1}',f'measure/schwefelFunction_{i+1}',f'analysis/dummy_{i+1}'], 
                params={f'wait_{i+1}':{'addresses':f'experiment_{i+1}:2/activeLearning_{2*i+2}'},
                        f'modify_{i+1}':{'addresses':[f'experiment_{i+1}:2/activeLearning_{2*i+2}/data/data/next_x',f'experiment_{i+1}:2/activeLearning_{2*i+2}/data/data/next_y'],'pointers':[f'schwefelFunction_{i+1}/x',f'schwefelFunction_{i+1}/y']},
                        f'schwefelFunction_{i+1}':{'x':'?','y':'?'},
                        f'dummy_{i+1}':{'x_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/x','y_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/parameters/y','schwefel_address':f'experiment_{i+1}:0/schwefelFunction_{i+1}/data/data/key_y'}}, meta=dict()),1)

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}),1)


test_fnc(dict(soe=['orchestrator/wait_0','ml/activeLearning_0'],
                  params = {'wait_0':{'addresses':'experiment_0:0/dummy_0'},
                            'activeLearning_0':{'query':query,'address':'experiment_0:0/dummy_0/data/data'}},meta={}),2)

for i in range(n):
    test_fnc(dict(soe=[f'orchestrator/wait_{2*i+1}',f'ml/activeLearning_{2*i+1}',f'orchestrator/wait_{2*i+2}',f'ml/activeLearning_{2*i+2}'],
                  params = {f'wait_{2*i+1}':{'addresses':f'experiment_{i}:1/dummy_{i}'},
                            f'activeLearning_{2*i+1}':{'query':query,'address':f'experiment_{i}:1/dummy_{i}/data/data'},
                            f'wait_{2*i+2}':{'addresses':f'experiment_{i+1}:0/dummy_{i+1}'},
                            f'activeLearning_{2*i+2}':{'query':query,'address':f'experiment_{i+1}:0/dummy_{i+1}/data/data'}},meta={}),2)

test_fnc(dict(soe=['orchestrator/finish'], params={'finish': None}, meta={}),2)