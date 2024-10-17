import sys
import h5py
import os
import requests
import json
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import math
#from celery import group

#from mischbares_small import config

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))


from util import hdf5_group_to_dict
from ml_driver import DataUtilSim
from importlib import import_module
config = import_module(sys.argv[1]).config
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
    global awaitedpoints
    awaitedpoints = {}


@app.get("/ml/receiveData")
def receiveData(path: str, run: int, address: str, modelid: int = 0):
    global data
    global awaitedpoints
    if modelid not in data.keys():
        data[modelid] = []
    if modelid not in awaitedpoints.keys():
        awaitedpoints[modelid] = []
    try:
        address = json.loads(address) # multiple
    except:
        address = [address]
    newdata = []
    #print(address)
    for add in address:
        with h5py.File(path, 'r') as h5file:
            add = f'run_{run}/'+add+'/'
            #print(add)
            if isinstance(h5file[add],h5py.Group):
                newdata.append(hdf5_group_to_dict(h5file, add))
            else:
                newdata.append(h5file[add][()])
            #print(newdata) # why is that a list?
    data[modelid].append(newdata[0] if len(newdata) == 1 else newdata)
    #print(f"newdata is {newdata}")
    #if newdata['x'] in awaitedpoints[modelid]:
    #    awaitedpoints[modelid].remove(newdata['x'])
    #print(data)
    #print("AP", awaitedpoints[modelid])

'''@app.get("/ml/gaus_model")
def gaus_model(length_scale: int = 1, restart_optimizer: int = 10, random_state: int = 42):
    model = d.gaus_model(length_scale, restart_optimizer, random_state)
    retc = return_class(parameters={'length_scale': length_scale, 'restart_optimizer': restart_optimizer, 'random_state': random_state}, data={
                        'model': model})
    return retc'''

# we still need to discuss about the data type that we are adding here.


@app.get("/ml/activeLearning")
def active_learning_random_forest_simulation(name: str, num: int, query: str, address: str, modelid=0):
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
    # with open('C:/Users/LaborRatte23-3/Documents/session/sessionLearning.pck', 'rb') as banana:
    #    sources = pickle.load(banana)
    # print(sources)
    global data
    #print("data", data)
    dat = data[modelid]
    #print("dat", dat)
    global awaitedpoints
    ap = awaitedpoints[modelid]
    next_exp_dx, next_exp_dy = d.active_learning_random_forest_simulation_parallel(name, num, query, dat, json.dumps(ap))
    awaitedpoints[modelid].append({'x':next_exp_dx, 'y':next_exp_dy})
    print(next_exp_dx, next_exp_dy)
    retc = return_class(parameters={'query': query, 'address': address, 'modelid': modelid}, data=dict(
        next_x=next_exp_dx, next_y=next_exp_dy))
    return retc

@app.get("/ml/activeLearningGaussian")
def active_learning_gaussian_simulation(name: str, num: int, query: str, address: str, modelid=0):
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
    # with open('C:/Users/LaborRatte23-3/Documents/session/sessionLearning.pck', 'rb') as banana:
    #    sources = pickle.load(banana)
    # print(sources)
    global data
    #print("data", data)
    dat = data[modelid]
    #print("dat", dat)
    global awaitedpoints
    ap = awaitedpoints[modelid]
    #beta = 0.4
    beta = math.exp(-0.05*num)
    next_exp_dx, next_exp_dy = d.active_learning_gaussian_simulation_parallel(name, num, query, dat, json.dumps(ap), beta)
    awaitedpoints[modelid].append({'x':next_exp_dx, 'y':next_exp_dy})
    print(next_exp_dx, next_exp_dy)
    retc = return_class(parameters={'query': query, 'address': address, 'modelid': modelid}, data=dict(
        next_x=next_exp_dx, next_y=next_exp_dy))
    return retc



'''@app.get("/ml/activeLearningParallel")
def active_learning_random_forest_simulation_parallel(name: str, num: int, query: str, address: str, modelid=0):
    global data
    dat = data[modelid]
    print(dat)
    #next_exp_dx, next_exp_dy, next_exp_dx_2, next_exp_dy_2 = d.active_learning_gaussian_simulation_parallel(num, query, dat)
    # check whether the point is already in waiting list or not
    global awaitedpoints
    ap = awaitedpoints[modelid]
    next_exp_dx, next_exp_dy = d.active_learning_random_forest_simulation_parallel(
        name, num, query, dat, json.dumps(ap))
    awaitedpoints[modelid].append({'x':next_exp_dx, 'y':next_exp_dy})
    # next_exp_pos : would be a [dx, dy] of the next move
    # prediction : list of predicted schwefel function for the remaning positions
    print(next_exp_dx, next_exp_dy)
    # return next_exp_pos[0], next_exp_pos[1], str(next_exp_pos)
    retc = return_class(parameters={'query': query, 'address': address, 'modelid': modelid}, data=dict(
        next_x=next_exp_dx, next_y=next_exp_dy))
    return retc'''


@app.get("ml/addData")
def addData(address: str, modelid=0):
    retc = return_class(
        parameters={'address': address, 'modelid': modelid}, data=None)
    return retc

@app.get("/ml/sdc4")
def active_learning_sdc_4(address: str, modelid=0):
    print(data[modelid])
    x = data[modelid][0][0][0]
    y = data[modelid][0][0][1]
    print("x and y:", x,y)
    #x = data[modelid][:][:2]
    #y = data[modelid][:][2]
    #y = y[:][-1]
    #df = pd.read_csv(r'C:\Users\LaborRatte23-2\Documents\SDC functions\Python scripts\df.csv').to_numpy()
    #XY, C, I, Q = df[:,0:2], df[:,2:5], df[:,-2], df[:,-1]
    ##x = np.array([[-6.25, 86.5],[-6.25, 91.5],[-11.25, 86.5]])
    #id_ = [np.where((XY == i).all(axis=1))[0][0] for i in x] # conversion of coordinates into ids of measured points
    #C_ = C[id_] # composition of all measured points
    #Q_ = y/3600*Q[id_] # capacity of all measured points
    #x_query = C_
    #y_query = Q_
    #train_ix = [x_query.index(j) for j in key_x]
    #regr = RandomForestRegressor(n_estimators=50,random_state=1337)
    #regr.fit(x,y)
    #pred = regr.predict(C)
    retc = return_class(parameters={'x':x,'y':y}, data={
                        'key_y': x+y})
    return retc

if __name__ == "__main__":
    d = DataUtilSim()
    print("instantiated ml server")
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'],
                port=config['servers'][serverkey]['port'])
