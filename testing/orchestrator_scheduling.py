# In order to run the orchestrator which is at the highest level of Helao, all servers should be started. 
import requests
import sys
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

@app.post("/addExperiment/")
def sendMeasurement(experiment: str):
    add_experiments.append(experiment)
    return {"message": experiment}

@app.post("/semiInfiniteLoop/")
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

@app.post("/infiniteLoop/")
def infiniteLoop(background_tasks: BackgroundTasks):
    background_tasks.add_task(infl)
    return {"message": 'bla'}

@app.post("/emergencyStop/")
def infiniteLoop():
    emergencyStop = True
    return {"message": 'bla'}

def doMeasurement(experiment: str):
    experiment = json.loads(experiment)
    print(experiment)
    for action_str,params in zip(experiment['soe'],experiment['params']):
        if not emergencyStop:
            server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
            action = fnc.split('_')[0]

            if server == 'movement':
                requests.get("http://{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'],server , action),
                                params= params).json
            elif server == 'pumping':
                requests.get("http://{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'],server, action),
                            params= params).json
            elif server == 'echem':
                requests.get("http://{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'],server, action),
                            params= params).json
            elif server == 'forceAction':
                requests.get("http://{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'],server, action),
                            params= params).json
            elif server == 'data':
                requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],server, action),
                            params= params).json
        else:
            print("Emergency stopped!")
            
if __name__ == "__main__":
    emergencyStop = False
    experiment_list = []
    add_experiments = []
    uvicorn.run(app, host= config['servers']['orchestrator']['host'], port= config['servers']['orchestrator']['port'])
    # run an example with
    # json.dumps({"soe": ["movement/moveToHome_0", "movement/moveUp_0", "movement/moveUp_1"], "params": {"moveToHome_0": None, "moveUp_0": {"z": 50}, "moveUp_1": {"z": -60}}})
    # {"soe": ["movement/moveToHome_0", "movement/moveUp_0"], "params": {"moveToHome_0": null, "moveUp_0": {"z": 50}}}
    #  {"soe": ["movement/moveToHome_0"], "params": {"moveToHome_0": null}}