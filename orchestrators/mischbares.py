# In order to run the orchestrator, which is at the highest level of Helao, all servers should be started.
from util import *
from numpy.lib.npyio import load
import requests
import sys
import os
import time
from fastapi import FastAPI, BackgroundTasks
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
config = import_module(sys.argv[1]).config

app = FastAPI(title="orchestrator",
              description="A fancy complex server", version=1.0)


@app.post("/orchestrator/addExperiment")
async def sendMeasurement(experiment: str):
    await experiment_queue.put(experiment)


async def infl():
    while True:
        experiment = await experiment_queue.get()
        await doMeasurement(experiment)


async def doMeasurement(experiment: str):
    global tracking, loop
    print('experiment: '+experiment)
    experiment = json.loads(experiment)  # load experiment
    # add header for new experiment if you already have initialized, nonempty experiment
    if isinstance(tracking['experiment'], int):
        with h5py.File(tracking['path'], 'r') as session:
            if len(list(session[f"/run_{tracking['run']}/experiment_{tracking['experiment']}"].keys())) > 0:
                tracking['experiment'] += 1
    # calculate measurement areas for meta dict if relevant
    if 'r' in experiment['meta'].keys() and 'ma' in experiment['meta'].keys():
        experiment['meta'].update(dict(measurement_areas=getCircularMA(
            experiment['meta']['ma'][0], experiment['meta']['ma'][1], experiment['meta']['r'])))
    for action_str in experiment['soe']:
        # Beispiel: action: 'movement' und fnc : 'moveToHome_0
        server, fnc = action_str.split('/')
        tracking['current_action'] = fnc
        action = fnc.split('_')[0]
        params = experiment['params'][fnc]
        if server == 'movement':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['movementServer']['host']}:{config['servers']['movementServer']['port']}/{server}/{action}")
        elif server == 'motor':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['motorServer']['host']}:{config['servers']['motorServer']['port']}/{server}/{action}")
        elif server == 'pumping':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['pumpingServer']['host']}:{config['servers']['pumpingServer']['port']}/{server}/{action}")
        elif server == 'minipumping':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['minipumpingServer']['host']}:{config['servers']['minipumpingServer']['port']}/{server}/{action}")
        elif server == 'echem':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['echemServer']['host']}:{config['servers']['echemServer']['port']}/{server}/{action}")
        elif server == 'forceAction':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['sensingServer']['host']}:{config['servers']['sensingServer']['port']}/{server}/{action}")
        elif server == 'table':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['tableServer']['host']}:{config['servers']['tableServer']['port']}/{server}/{action}")
        elif server == 'oceanAction':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), f"http://{config['servers']['ramanServer']['host']}:{config['servers']['ramanServer']['port']}/{server}/{action}")
        elif server == 'data':
            await loop.run_in_executor(None, lambda x: requests.get(x, params=params), f"http://{config['servers']['dataServer']['host']}:{config['servers']['dataServer']['port']}/{server}/{action}")
            continue
        elif server == 'orchestrator':
            if params == None:
                params = {}
            experiment = await loop.run_in_executor(None, lambda c, e: process_native_command(c, e, **params), action, experiment)
            continue
        elif server == 'analysis':
            continue
        elif server == 'learning':
            continue
        save_dict_to_hdf5({fnc: {'data': res, 'measurement_time': datetime.datetime.now().strftime(
            "%d/%m/%Y, %H:%M:%S")}}, tracking['path'], path=f"/run_{tracking['run']}/experiment_{tracking['experiment']}/", mode='a')
        with h5py.File(tracking['path'], 'r') as session:  # add metadata to experiment
            l = list(
                session[f"/run_{tracking['run']}/experiment_{tracking['experiment']}"].keys())
            # disregard if you did not do any real actions this experiment, or if meta already added
            if len(l) > 0 and 'meta' not in l:
                session.close()
                save_dict_to_hdf5({'meta': experiment['meta']}, tracking['path'],
                                  path=f"/run_{tracking['run']}/experiment_{tracking['experiment']}/", mode='a')


def process_native_command(command: str, experiment: dict, **params):
    # try:
    return getattr(sys.modules[__name__], command)(experiment, **params)
    # except:#except what?
    #    raise Exception("native command not recognized")


def start(experiment: dict, **params):
    global tracking
    h5dir = os.path.join(config['orchestrator']['path'],
                         f"{params['collectionkey']}_{experiment['meta'][params['collectionkey']]}")
    # ensure that the directory in which this session should be saved exists
    if not os.path.exists(h5dir):
        os.mkdir(h5dir)
    if os.listdir(h5dir) == []:  # if dir is empty, create a session
        tracking['path'] = os.path.join(
            h5dir, os.path.basename(h5dir)+'_session_0.hdf5')
        save_dict_to_hdf5(dict(
            meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))), tracking['path'])
    else:  # otherwise grab most recent session in dir
        tracking['path'] = os.path.join(h5dir, highestName(
            list(filter(lambda s: s[-5:] == '.hdf5', os.listdir(h5dir)))))
    with h5py.File(tracking['path'], 'r') as session:
        # assigns date to this session if necessary, or replaces session if too old
        if 'date' not in session['meta'].keys():
            session.close()
            save_dict_to_hdf5(dict(date=datetime.date.today().strftime(
                "%d/%m/%Y")), tracking['path'], path='/meta/', mode='a')
        elif session['meta']['date'] != datetime.date.today().strftime("%d/%m/%Y"):
            print(
                'current session is old, saving current session and creating new session')
            session.close()
            try:
                print(requests.get(f"http://{config['servers']['dataServer']['host']}:{config['servers']['dataServer']['port']}/{'data'}/{'uploadhdf5'}",
                                   params=dict(filename=os.path.basename(tracking['path']), filepath=os.path.dirname(tracking['path']))).json())
            except:
                print('automatic upload of completed session failed')
            tracking['path'] = os.path.join(
                h5dir, incrementName(os.path.basename(tracking['path'])))
            save_dict_to_hdf5(dict(
                meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))), tracking['path'])
    # adds a new run to session to receive incoming data
    with h5py.File(tracking['path'], 'r') as session:
        if "run_0" not in session.keys():
            session.close()
            save_dict_to_hdf5(
                dict(run_0=dict(experiment_0=None, meta=params)), tracking['path'], mode='a')
            tracking['run'] = 0
        else:
            # don't put any keys in here that have length less than 4 i guess
            run = incrementName(highestName(
                list(filter(lambda k: k[:4] == "run_", list(session.keys())))))
            session.close()
            save_dict_to_hdf5(
                {run: dict(experiment_0=None, meta=params)}, tracking['path'], mode='a')
            tracking['run'] = int(run[4:])
    tracking['experiment'] = 0
    save_dict_to_hdf5(
        {'meta': None}, tracking['path'], path=f'/run_{tracking["run"]}/experiment_0/', mode='a')
    return experiment


def finish(experiment: dict, **params):
    global tracking
    print('attempting to upload session')
    try:
        print(requests.get(f"http://{config['servers']['dataServer']['host']}:{config['servers']['dataServer']['port']}/{'data'}/{'uploadhdf5'}",
                           params=dict(filename=os.path.basename(tracking['path']), filepath=os.path.dirname(tracking['path']))).json())
    except:
        print('automatic upload of completed session failed')

    tracking['path'] = os.path.join(os.path.dirname(
        tracking['path']), incrementName(os.path.basename(tracking['path'])))
    tracking['run'] = None
    tracking['experiment'] = None
    tracking['current_action'] = None
    save_dict_to_hdf5(dict(meta=None), tracking['path'])
    # adds a new hdf5 file which will be used for the next incoming data, thus sealing off the previous one
    return experiment


@app.on_event("startup")
async def memory():
    global tracking
    # a dict of useful variables to keep track of -- one day should all just be part of a GUI
    tracking = {'path': None, 'run': None,
                'experiment': None, 'current_action': None}
    global experiment_queue
    experiment_queue = asyncio.Queue()
    global task
    task = asyncio.ensure_future(infl())
    global loop
    loop = asyncio.get_event_loop()
    global error
    error = loop.create_task(raise_exceptions())


@app.on_event("shutdown")
def disconnect():
    global task, error
    if not error.cancelled():
        error.cancel()
    if not task.cancelled():
        task.cancel()

# error handing within the infinite loop
# check for exceptions. if found, print stack trace and cancel infinite loop


async def raise_exceptions():
    global task
    while True:
        # check for errors every second (maybe this should be a different number?)
        await asyncio.sleep(1)
        try:
            task.exception()
            task.print_stack()  # it seems like this maybe lies a bit sometimes
            task.cancel()
            error.cancel()
        except:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host=config['servers']['orchestrator']
                ['host'], port=config['servers']['orchestrator']['port'])
