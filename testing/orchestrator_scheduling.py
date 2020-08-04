# In order to run the orchatrator which is at the highest level of Helao, all servers should be started. 
import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from mischbares_small import config
from fastapi import FastAPI
from pydantic import BaseModel,BackgroundTasks
import json
import uvicorn
from typing import List
from fastapi import FastAPI, Query
import json

app = FastAPI(title = "orchestrator", description = "A fancy complex server",version = 1.0)

@app.post("/addExperiment/{experiment}")
def sendMeasurement(experiment: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(doMeasurement, experiment)
    return {"message": message}

def doMeasurement(experiment: str):
    experiment_list = addToQueue(experiment)
    for action_str in experiment_list[0]['soe']:

        server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
        action = fnc.split('_')[0]

        if server == 'movement':
            requests.get("https//{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'],server , action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'pumping':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'echem':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'forceAction':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        elif server == 'data':
            requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],server, action),
                        params= experiment_list[0]['params'][fnc]).json
        
if __name__ == "__main__":
    uvicorn.run(app, host= config['servers']['orchestrator']['host'], port= config['servers']['orchestrator']['port'])
    # run an example with
    '{"soe": ["movement/moveToHome_0", "movement/moveUp_0", "movement/moveUp_1"], "params": {"moveToHome_0": null, "moveUp_0": {"z": 50}, "moveUp_1": {"z": -60}}}'

