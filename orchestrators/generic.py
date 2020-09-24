import sys
import os
import json
import time
import requests
from typing import List
from copy import copy
from importlib import import_module

import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi import FastAPI, Query
from pydantic import BaseModel
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
O = C[servKey]

app = FastAPI(title=servKey,
              description="A generic orchestrator", version=1.0)


@app.post(f"/{servKey}/addExperiment")
def sendMeasurement(experiment: str):
    add_experiments.append(experiment)
    return {"message": experiment}


@app.post(f"/{servKey}/semiInfiniteLoop")
async def semiInfiniteLoop():
    while True:
        #for reasons of changing list lens:
        numToAdd = copy(len(add_experiments))
        if numToAdd > 0:
            for i in range(numToAdd):
                experiment_list.append(add_experiments.pop(0))
        #for reasons of changing list lens:
        numToMeasure = copy(len(experiment_list))
        if numToMeasure > 0:
            for i in range(numToMeasure):
                doMeasurement(experiment_list.pop(0))
        else:
            break


def infl():
    while True:
        #for reasons of changing list lens:
        numToAdd = copy(len(add_experiments))
        if numToAdd > 0:
            for i in range(numToAdd):
                experiment_list.append(add_experiments.pop(0))
        #for reasons of changing list lens:
        numToMeasure = copy(len(experiment_list))
        if numToMeasure > 0:
            for i in range(numToMeasure):
                doMeasurement(experiment_list.pop(0))
        else:
            time.sleep(0.5)
        if emergencyStop:
            break


@app.post(f"/{servKey}/infiniteLoop")
def infiniteLoop(background_tasks: BackgroundTasks):
    background_tasks.add_task(infl)
    return {"message": 'bla'}


@app.post(f"/{servKey}/emergencyStop")
def stopInfiniteLoop():
    emergencyStop = True
    return {"message": 'bla'}


def doMeasurement(experiment: str):
    experiment = json.loads(experiment)
    print(experiment)
    for action_str in experiment['soe']:
        if not emergencyStop:
            #print(action_str)
            # Beispiel: action: 'movement' und fnc : 'moveToHome_0
            server, action = action_str.split('/')
            #print(server)
            #print(fnc)
            # action = fnc.split('_')[0]
            params = experiment['params']
            #print(action)
            #print(params)
            S = C[server]
            res = requests.get(f"http://{S.host}:{S.port}/{server}/{action}", params=params).json()
            # substrate = experiment['meta']['substrate']
            # ma = experiment['meta']['ma']
            with open(os.path.join(O.path, f'{time.time_ns()}_{server}_{action}.json'), 'w') as f:
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
    uvicorn.run(app, host=O.host, port=O.port)
    
