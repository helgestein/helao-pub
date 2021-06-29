# In order to run the orchestrator, which is at the highest level of Helao, all servers should be started. 
from numpy.lib.npyio import load
import requests
import sys
import os
import time
from fastapi import FastAPI,BackgroundTasks
from pydantic import BaseModel
import json
from copy import copy
import uvicorn
from typing import List
from fastapi import FastAPI, Query
import json
import h5py
import datetime
import asyncio
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
sys.path.append(os.path.join(helao_root, 'config'))
from util import *
config = import_module(sys.argv[1]).config

app = FastAPI(title = "orchestrator", description = "A fancy complex server",version = 1.0)



@app.post("/orchestrator/addExperiment")
async def sendMeasurement(experiment: str):
    await experiment_queue.put(experiment)

async def infl():
    while True:
        experiment = await experiment_queue.get()
        await doMeasurement(experiment)

async def doMeasurement(experiment: str):
    print(asyncio.get_running_loop().get_exception_handler())
    raise Exception("they'll be dead soon, fucking kangaroos")
    global tracking,loop
    print('experiment: '+experiment)
    experiment = json.loads(experiment) # load experiment
    if isinstance(tracking['experiment'],int): # add header for new experiment if you already have initialized, nonempty experiment
        with h5py.File(tracking['path'], 'r') as session:
            if session[f"/run_{tracking['run']}/experiment_{tracking['experiment']}"].keys() != ['meta']:
                assert len(session[f"/run_{tracking['run']}/experiment_{tracking['experiment']}"].keys()) > 1
                tracking['experiment'] += 1
    if 'r' in experiment['meta'].keys() and 'ma' in experiment['meta'].keys(): #calculate measurement areas for meta dict if relevant
        experiment['meta'].update(dict(measurement_areas=getCircularMA(experiment['meta']['ma'][0],experiment['meta']['ma'][1],experiment['meta']['r'])))
    for action_str in experiment['soe']:
        server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
        tracking['current_action'] = fnc
        action = fnc.split('_')[0]
        params = experiment['params'][fnc]
        if server == 'movement':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'],server,action))
        elif server == 'motor':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['motorServer']['host'], config['servers']['motorServer']['port'],server,action))
        elif server == 'pumping':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'],server,action))
        elif server == 'minipumping':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['minipumpingServer']['host'], config['servers']['minipumpingServer']['port'],server,action))
        elif server == 'echem':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'],server,action))
        elif server == 'forceAction':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'],server,action))
        elif server == 'table':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['tableServer']['host'], config['servers']['tableServer']['port'],server,action))
        elif server == 'oceanAction':
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),"http://{}:{}/{}/{}".format(config['servers']['ramanServer']['host'], config['servers']['ramanServer']['port'],server,action))
        elif server == 'data':
            await loop.run_in_executor(None,lambda x: requests.get(x,params=params),"http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],server,action))
            continue
        elif server == 'orchestrator':
            experiment = await loop.run_in_executor(None,lambda c,e: process_native_command(c,e,**params),action,experiment)
            continue
        elif server == 'analysis':
            continue
        elif server == 'learning':
            continue
        save_dict_to_hdf5({fnc:{'data':res,'measurement_time':datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}},tracking['path'],path=f"/run_{tracking['run']}/experiment_{tracking['experiment']}",mode='a')
    save_dict_to_hdf5({'meta':experiment['meta']},tracking['path'],path=f"run_{tracking['run']}/experiment_{tracking['experiment']}",mode='a') #add metadata to experiment

def process_native_command(command: str,experiment: dict,**params):
    #try:
    return getattr(sys.modules[__name__],command)(experiment,**params)
    #except:#except what?
    #    raise Exception("native command not recognized")


def start(experiment: dict,**params):
    global tracking
    h5dir = os.path.join(config['orchestrator']['path'],f"{params['collectionkey']}_{experiment['meta'][params['collectionkey']]}")
    if not os.path.exists(h5dir): #ensure that the directory in which this session should be saved exists
        os.mkdir(experiment['meta']['path'])
    if os.listdir(h5dir) == []: #if dir is empty, create a session
        tracking['path'] = os.path.join(h5dir,os.path.basename(h5dir)+'_session_0.hdf5')
        save_dict_to_hdf5(dict(meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))),tracking['path'])
    else: #otherwise grab most recent session in dir
        tracking['path'] = os.path.join(h5dir,highestName(list(filter(lambda s: s[-5:]=='.hdf5',os.listdir(h5dir)))))
    with h5py.File(tracking['path'], 'r') as session:
        print("session on")
        if 'date' not in session['meta'].keys(): #assigns date to this session if necessary, or replaces session if too old
            session.close()
            print("give date")
            save_dict_to_hdf5(dict(date=datetime.date.today().strftime("%d/%m/%Y")),tracking['path'],path='/meta',mode='a')
        elif session['meta']['date'] != datetime.date.today().strftime("%d/%m/%Y"):
            print('current session is old, saving current session and creating new session')
            session.close()
            try:
                print(requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],'data','uploadhdf5'),
                        params=dict(filename=os.path.basename(tracking['path']),filepath=os.path.dirname(tracking['path']))).json())
            except:
                print('automatic upload of completed session failed')
            tracking['path'] = os.path.join(h5dir,incrementName(os.path.basename(tracking['path'])))
            save_dict_to_hdf5(dict(meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))),tracking['path'])
    print("here2")
    with h5py.File(tracking['path'], 'r') as session: #adds a new run to session to receive incoming data
        if "run_0" not in session.keys(): 
            session.close()
            save_dict_to_hdf5(dict(run_0=dict(experiment_0={},meta=params)),tracking['path'],mode='a')
            tracking['run'] = 0
        else:
            run = incrementName(highestName(list(filter(lambda k: k[:4]=="run_",list(session.keys()))))) #don't put any keys in here that have length less than 4 i guess
            session.close()
            save_dict_to_hdf5({run:dict(experiment_0={},meta=params)},tracking['path'],mode='a')
            tracking['run'] = int(run[4:])
    tracking['experiment'] = 0
    save_dict_to_hdf5({'meta':None},tracking['path'],path=f'/run_{run}/experiment_0',mode='a')
    print("here3")
    return experiment

def finish(experiment: dict,**params):
    global tracking
    print('attempting to upload session')
    try:
        print(requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'],'data','uploadhdf5'),
                        params=dict(filename=os.path.basename(tracking['path']),filepath=os.path.dirname(tracking['path']))).json())
    except:
        print('automatic upload of completed session failed')
    
    tracking['path'] = os.path.join(os.path.dirname(tracking['path']),incrementName(os.path.basename(tracking['path'])))
    tracking['run'] = None
    tracking['experiment'] = None
    tracking['current_action'] = None
    save_dict_to_hdf5(dict(meta=dict()),tracking['path'])
    #adds a new hdf5 file which will be used for the next incoming data, thus sealing off the previous one
    return experiment
    





@app.on_event("startup")
async def memory():
    global tracking
    tracking = {'path':None,'run':None,'experiment':None,'current_action':None} #a dict of useful variables to keep track of -- one day should all just be part of a GUI
    global experiment_queue
    experiment_queue = asyncio.Queue()
    global task
    task = asyncio.create_task(infl())
    global loop
    loop = asyncio.get_event_loop()
    global error
    error = asyncio.create_task(raise_exceptions())

@app.on_event("shutdown")
def disconnect():
    global task, error
    error.cancel()
    task.cancel()
            
async def raise_exceptions():
    global task
    await task


if __name__ == "__main__":
    uvicorn.run(app, host= config['servers']['orchestrator']['host'], port= config['servers']['orchestrator']['port'])