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
from fastapi.openapi.utils import get_flat_params
from munch import munchify

# not packaging as module for now, so detect source code's root directory from CLI execution
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# append config folder to path to allow dynamic config imports
sys.path.append(os.path.join(helao_root, 'config'))
# grab config file prefix (e.g. "world" for world.py) from CLI argument
confPrefix = sys.argv[1]
# grab server key from CLI argument, this is a unique name for the server instance
servKey = sys.argv[2]
# import config dictionary
config = import_module(f"{confPrefix}").config
# shorthand object-style access to config dictionary
C = munchify(config)["servers"]
# config dict for visualization server
O = C[servKey]

app = FastAPI(title=servKey,
              description="Helao world demo orchestrator", version=1.0)


@app.on_event("startup")
def startup_event():
    global blockd
    blockd = {}

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
            res = requests.post(f"http://{S.host}:{S.port}/{server}/{action}", params=params).json()
            # substrate = experiment['meta']['substrate']
            # ma = experiment['meta']['ma']
            with open(os.path.join(O.path, f'{time.time_ns()}_{server}_{action}.json'), 'w') as f:
                json.dump(res, f)
        else:
            print("Emergency stopped!")


@app.post('/endpoints')
def get_all_urls():
    url_list = []
    for route in app.routes:
        routeD = {'path': route.path,
                  'name': route.name
                  }
        if 'dependant' in dir(route):
            flatParams = get_flat_params(route.dependant)
            paramD = {par.name: {
                'outer_type': str(par.outer_type_).split("'")[1],
                'type': str(par.type_).split("'")[1],
                'required': par.required,
                'shape': par.shape,
                'default': par.default
            } for par in flatParams}
            routeD['params'] = paramD
        else:
            routeD['params'] = []
        url_list.append(routeD)
    return url_list


@app.on_event("shutdown")
def disconnect():
    emergencyStop = True
    time.sleep(0.75)


if __name__ == "__main__":
    emergencyStop = False
    experiment_list = []
    add_experiments = []
    uvicorn.run(app, host=O.host, port=O.port)
    
