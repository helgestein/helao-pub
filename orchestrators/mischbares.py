# In order to run the orchestrator which is at the highest level of Helao, all servers should be started. 
import requests
import sys
import os
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from mischbares_small import config
from fastapi import FastAPI,BackgroundTasks
from pydantic import BaseModel
import json
from copy import copy
import uvicorn
from typing import List
from fastapi import FastAPI, Query
import json

app = FastAPI(title = "orchestrator", description = "A fancy complex server",version = 1.0)

@app.post("/orchestrator/addExperiment")
def sendMeasurement(experiment: str):
    add_experiments.append(experiment)
    return {"message": experiment}

@app.post("/orchestrator/semiInfiniteLoop")
async def semiInfiniteLoop():
    while True:
        #for reasons of changing list lens:
        numToAdd = copy(len(add_experiments))
        if numToAdd>0:
            for i in range(numToAdd):
                experiment_list.append(add_experiments.pop(0))
        #for reasons of changing list lens:
        numToMeasure = copy(len(experiment_list))
        if numToMeasure>0:
            for i in range(numToMeasure):
                doMeasurement(experiment_list.pop(0))
        else:
            break

def infl():
    while True:
        #for reasons of changing list lens:
        numToAdd = copy(len(add_experiments))
        if numToAdd>0:
            for i in range(numToAdd):
                experiment_list.append(add_experiments.pop(0))
        #for reasons of changing list lens:
        numToMeasure = copy(len(experiment_list))
        if numToMeasure>0:
            for i in range(numToMeasure):
                doMeasurement(experiment_list.pop(0))
        else:
            time.sleep(0.5)
        if emergencyStop:
            break

@app.post("/orchestrator/infiniteLoop")
def infiniteLoop(background_tasks: BackgroundTasks):
    background_tasks.add_task(infl)
    return {"message": 'bla'}

@app.post("/orchestrator/emergencyStop")
def stopInfiniteLoop():
    emergencyStop = True
    return {"message": 'bla'}

def doMeasurement(experiment: str):
    experiment = json.loads(experiment)
    print(experiment)
    for action_str in experiment['soe']:
        if not emergencyStop:
            #print(action_str)
            server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
            #print(server)
            #print(fnc)
            action = fnc.split('_')[0]
            params = experiment['params'][fnc]
            #print(action)
            #print(params)
            if server == 'movement':
                res = requests.get("http://{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'],server , action),
                                params= params).json()
            elif server == 'motor':
                res = requests.get("http://{}:{}/{}/{}".format(config['servers']['motorServer']['host'], config['servers']['motorServer']['port'],server , action),
                                params= params).json()
            elif server == 'pumping':
                res = requests.get("http://{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'],server, action),
                            params= params).json()
            elif server == 'echem':
                res = requests.get("http://{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'],server, action),
                            params= params).json()
            elif server == 'forceAction':
                res = requests.get("http://{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'],server, action),
                            params= params).json()
                print(res)
            elif server == 'data':
                res = requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],server, action),
                            params= params).json()
            substrate= experiment['meta']['substrate']
            ma = experiment['meta']['ma']
            with open(os.path.join(config['orchestrator']['path'],'{}_{}_{}_{}_{}.json'.format(time.time_ns(),str(substrate),str(ma),server,action)), 'w') as f:
                json.dump(res, f)
        else:
            print("Emergency stopped!")
    
@app.on_event("shutdown")
def disconnect():
    emergencyStop = True
    time.sleep(0.75)
            
if __name__ == "__main__":
    emergencyStop = False
    experiment_list = []
    add_experiments = []
    uvicorn.run(app, host= config['servers']['orchestrator']['host'], port= config['servers']['orchestrator']['port'])
    # run an example with
    # json.dumps({"soe": ["movement/moveToHome_0", "movement/moveUp_0", "movement/moveUp_1"], "params": {"moveToHome_0": None, "moveUp_0": {"z": 50}, "moveUp_1": {"z": -60}}})
    # {"soe": ["movement/moveToHome_0", "movement/moveUp_0"], "params": {"moveToHome_0": null, "moveUp_0": {"z": 50}}}
    #  {"soe": ["movement/moveToHome_0"], "params": {"moveToHome_0": null}}
    '''
    B = dict(
        soe=['movement/moveToHome_0','movement/alignment_0','movement/mvToWaste_0','pumping/formulation_0',
        'movement/removeDrop_0','movement/moveToHome_1','movement/mvToSample_0',
        'echem/measure_0','pump/formulation_1','movement/moveToHome_2','movement/mvToWaste_1',
        'pumping/formulation_2','movement/removeDrop_1','movement/moveToHome_3','movement/mvToSample_1',
        'echem/measure_1','pump/formulation_3'], 
        params = dict(  moveToHome_0 = None,
                        alignment_0 = None,
                        mvToWaste_0 = dict(x= 0.0,y= 0.0),
                        formulation_0 = dict(formulation= [0.2,0.2,0.2,0.2,0.2],
                                            pumps= [0,1,2,3,4],
                                            speed= 1000,
                                            direction= -1,
                                            stage= True,
                                            totalVol= 2000),
                        removeDrop_0 = dict(y= -20),
                        moveToHome_1 = None,
                        mvToSample_0 = dict(x= 20, y= 10),
                        measure_0= dict(procedure= 'ca',
                                        setpoints= dict(applypotential = {'Setpoint value': -0.5},
                                                        recordsignal= {'Duration': 300}),
                                    plot= False,
                                    onoffafter= 'off'),
                        formulation_1 = dict(formulation=[1],
                                            pumps=[5],
                                            speed=4000,
                                            direction=1,
                                            stage=True,
                                            totalVol=2000),
                        moveToHome_2 = None,
                        mvToWaste_1 = dict(position= {'x':0.0,'y':0.0}),
                        formulation_2 = dict(formulation= [2],
                                            pumps= [5],
                                            speed= 4000,
                                            direction= 1,
                                            stage= True,
                                            totalVol= 2000), 
                        removeDrop_1 = dict(y = -20), 
                        moveToHome_3 = None,
                        mvToSample_1 = dict(x= 18, y= 8), 
                        measure_1= dict(procedure= 'ca',
                                        setpoints= dict(applypotential = {'Setpoint value': -0.5},
                                                        recordsignal= {'Duration': 300}),
                                        plot= False,
                                        onoffafter= 'off'),
                        formulation_3 = dict(formulation=[1],
                                            pumps=[5],
                                            speed=4000,
                                            direction=1,
                                            stage=True,
                                            totalVol=2000)),
        exp_name = 'B')

    


    global_experiment_list = [A]
    #addrecord_0= dict(ident= 1,title= 'electrodeposition', filed= 'cu-No3', visibility='private',meta=None)
        
    #experiment = json.dumps(experiment_spec)

    uvicorn.run(app, host= config['servers']['orchestrator']['host'], port= config['servers']['orchestrator']['port'])
    print("orchestrator is instantiated. ")

    

    {"soe": ["movement/moveToHome_0", "movement/alignment_0", "movement/mvToWaste_0", "pumping/formulation_0", "movement/removeDrop_0", 
    "movement/moveToHome_1", "movement/mvToSample_0", "echem/measure_0", "pump/formulation_1", "movement/moveToHome_2", "movement/mvToWaste_1", 
    "pumping/formulation_2", "movement/removeDrop_1", "movement/moveToHome_4", "movement/mvToSample_1", "echem/measure_1", "pump/formulation_3"], 
    "params": {"moveToHome_0": null, "alignment_0": null, "mvToWaste_0": {"x": 0.0, "y": 0.0}, "formulation_0": {"formulation": [0.2, 0.2, 0.2, 0.2, 0.2], 
    "pumps": [0, 1, 2, 3, 4], "speed": 1000, "direction": -1, "stage": true, "totalVol": 2000}, "removeDrop_0": {"y": -20}, 
    "moveToHome_1": null, "mvToSample_0": {"x": 20, "y": 10}, "measure_0": {"procedure": "ca", "setpoints": {"applypotential": {"Setpoint value": -0.5}, 
    "recordsignal": {"Duration": 300}}, "plot": false, "onoffafter": "off"}, "fomulation_1": {"formulation": [1], "pumps": [5], "speed": 4000, "direction": 1, 
    "stage": true, "totalVol": 2000}, "moveToHome_2": null, "mvToWaste_1": {"position": {"x": 0.0, "y": 0.0}}, 
    "fomulation_2": {"formulation": [1], "pumps": [5], "speed": 4000, "direction": 1, "stage": true, "totalVol": 2000}, 
    "removeDrop_1": {"y": -20}, "moveToHome_3": null, "mvToSample_1": {"x": 18, "y": 8}, "measure_1": {"procedure": "ca", 
    "setpoints": {"applypotential": {"Setpoint value": -0.5}, "recordsignal": {"Duration": 300}}, "plot": false, "onoffafter": "off"}, 
    "fomulation_3": {"formulation": [1], "pumps": [5], "speed": 4000, "direction": 1, "stage": true, "totalVol": 2000}}}

    '''

