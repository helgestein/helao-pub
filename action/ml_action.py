import sys
sys.path.append(r'../driver')
sys.path.append(r'../action')
sys.path.append(r'../config')
#from mischbares_small import config

from celery import group
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import os
import h5py
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
from ml_driver import DataUtilSim
from util import hdf5_group_to_dict
serverkey = sys.argv[2]

app = FastAPI(title="analysis action server",
              description="This is a test measure action",
              version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.on_event("startup")
def memory():
    global data
    data = {}

@app.get("/ml/receiveData")
def receiveData(path:str,run:int,address:str,modelid:int=0):
    global data
    if modelid not in data.keys():
        data[modelid] = []
    with h5py.File(path,'r') as h5file:
        address = f'run_{run}/'+address+'/'
        data[modelid].append(hdf5_group_to_dict(h5file,address))
    print(data)

@app.get("/ml/gaus_model")
def gaus_model(length_scale: int = 1, restart_optimizer: int = 10, random_state: int = 42):
    model = d.gaus_model(length_scale, restart_optimizer, random_state)
    retc = return_class(parameters={'length_scale': length_scale, 'restart_optimizer': restart_optimizer, 'random_state': random_state}, data={
                        'model': model})
    return retc

# we still need to discuss about the data type that we are adding here.


@app.get("/ml/activeLearning")
def active_learning_random_forest_simulation(query: str, address: str, modelid=0):
    """
    if sources == "session":
        sources = requests.get("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'], 
                config['servers']['orchestrator']['port'], 'orchestrator', 'getSession'), params=None).json()
    else:
        try:
            sources = json.loads(sources)
            if "session" in sources:
                sources[sources.index("session")] = requests.get("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'], 
                config['servers']['orchestrator']['port'], 'orchestrator', 'getSession'), params=None).json()
        except:
            pass
    """  
    #with open('C:/Users/LaborRatte23-3/Documents/session/sessionLearning.pck', 'rb') as banana:
    #    sources = pickle.load(banana)  
    #print(sources)
    global data
    dat = data[modelid]

    next_exp_dx, next_exp_dy  = d.active_learning_random_forest_simulation(query,dat)

    # next_exp_pos : would be a [dx, dy] of the next move
    # prediction : list of predicted schwefel function for the remaning positions
    print(next_exp_dx, next_exp_dy, next_exp_pos)
    #return next_exp_pos[0], next_exp_pos[1], str(next_exp_pos)
    retc = return_class(parameters = {'query':query,'address':address,'modelid':modelid}, data = dict(next_x = next_exp_dx, next_y = next_exp_dy))
    return retc
  
if __name__ == "__main__":
    d = DataUtilSim()
    print("instantiated ml server")
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                port=config['servers'][serverkey]['port'])
