# In order to run the orchestrator which is at the highest level of Helao, all servers should be started.
import sys
import os
import json
import datetime
import time
from typing import List
from copy import copy
from fastapi import FastAPI
import uvicorn
import requests
from pydantic import BaseModel
import hdfdict
import asyncio
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(helao_root)
from util import *
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
    global session, sessionname, loop
    print('experiment: '+experiment)
    experiment = json.loads(experiment)
    experiment['meta'].update(dict(path=os.path.join(
        config['orchestrator']['path'], f"substrate_{experiment['meta']['substrate']}")))
    # get the provisional run and measurement number
    if session == None:
        experiment['meta'].update(dict(run=None, measurement_number=None))
    else:
        experiment['meta'].update(dict(run=int(highestName(
            list(filter(lambda k: k[:4] == "run_", list(session.keys()))))[4:])))
        measurement = highestName(list(filter(
            lambda k: k != 'meta', session[f"run_{experiment['meta']['run']}"].keys())))
        # don't add a new measurement if last measurement was empty
        if list(session[f"run_{experiment['meta']['run']}"][measurement].keys()) == ['meta']:
            experiment['meta'].update(
                dict(measurement_number=int(measurement[15:])))
        else:
            experiment['meta'].update(
                dict(measurement_number=int(measurement[15:])+1))
    experiment['meta'].update(dict(measurement_areas=getCircularMA(
        experiment['meta']['ma'][0], experiment['meta']['ma'][1], experiment['meta']['r'])))
    if experiment['meta']['measurement_number'] != None:
        session[f"run_{experiment['meta']['run']}"].update({f"measurement_no_{experiment['meta']['measurement_number']}": {
                                                           'meta': {'measurement_areas': experiment['meta']['measurement_areas']}}})
    for action_str in experiment['soe']:
        experiment['meta'].update(dict(current_action=action_str))
        # Beispiel: action: 'movement' und fnc : 'moveToHome_0
        server, fnc = action_str.split('/')
        action = fnc.split('_')[0]
        params = experiment['params'][fnc]
        if server == 'movement':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['movementServer']['host'], config['servers']['movementServer']['port'], server, action))
        elif server == 'motor':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['motorServer']['host'], config['servers']['motorServer']['port'], server, action))
        elif server == 'pumping':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['pumpingServer']['host'], config['servers']['pumpingServer']['port'], server, action))
        elif server == 'minipumping':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['minipumpingServer']['host'], config['servers']['minipumpingServer']['port'], server, action))
        elif server == 'echem':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['echemServer']['host'], config['servers']['echemServer']['port'], server, action))
        elif server == 'forceAction':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['sensingServer']['host'], config['servers']['sensingServer']['port'], server, action))
            print(res)
        elif server == 'table':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['tableServer']['host'], config['servers']['tableServer']['port'], server, action))
        elif server == 'oceanAction':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['smallRamanServer']['host'], config['servers']['smallRamanServer']['port'], server, action))
        elif server == 'data':
            await loop.run_in_executor(None, lambda x: requests.get(x, params=params), "http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'], server, action))
            continue
        elif server == 'measure':
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['measureServer']['host'], config['servers']['measureServer']['port'], server, action))
        elif server == 'orchestrator':
            experiment = await loop.run_in_executor(None, process_native_command, action, experiment)
            continue
        elif server == 'analysis':
            if params['sources'] == "session":
                params['sources'] = json.dumps(session, cls=NumpyArrayEncoder)
            else:
                try:
                    sources = json.loads(params['sources'])
                    if "session" in sources:
                        sources[sources.index("session")] = session
                        params['sources'] = json.dumps(sources, cls=NumpyArrayEncoder)
                except:
                    pass
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['analysisServer']['host'], config['servers']['analysisServer']['port'], server, action))        
        elif server == 'learning':
            if params['sources'] == "session":
                params['sources'] = json.dumps(session, cls=NumpyArrayEncoder)
            else:
                try:
                    sources = json.loads(params['sources'])
                    if "session" in sources:
                        sources[sources.index("session")] = session
                        params['sources'] = json.dumps(sources, cls=NumpyArrayEncoder)            
                except:
                    pass
            try:
                pointers = json.loads(params['pointers'])
            except:
                pointers = params['pointers']
            params = {x: params[x] for x in params if x != 'pointers'}
            res = await loop.run_in_executor(None, lambda x: requests.get(x, params=params).json(), "http://{}:{}/{}/{}".format(config['servers']['learningServer']['host'], config['servers']['learningServer']['port'], server, action))
            experiment = process_native_command(
                "modify", experiment, vals=res, pointers=pointers)
            continue
        session[f"run_{experiment['meta']['run']}"][f"measurement_no_{experiment['meta']['measurement_number']}"].update(
            {fnc: {'data': res, 'measurement_time': datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}})
        # provisionally dumping every time until proper backup implemented
        hdfdict.dump(session, os.path.join(experiment['meta']['path'], sessionname+'.hdf5'), mode='w')
        # with open(os.path.join(config['orchestrator']['path'],'{}_{}_{}_{}_{}.json'.format(time.time_ns(),str(substrate),str(ma),server,action)), 'w') as f:
        #    json.dump(res, f)

#ways: store result of a previous calculation in session, and be clear that future things no where to find it (cumbersome to put a modify call everywhere)
#have the call modify all future values at once (unable to hit experiments beyond the current one)
#give actions global memory (I like this idea better...)
#now what about looping feedback?
#i probably have to make a few native commands for that, right?
#so we want a loop that can repeat a series of actions, ending on an arbitrary condition?
#we need to figure out how to encode the condition
#additionally, given that I can modify an experiment but am not adding new ones, we are still blurring the line with experiments somewhat. need to clarify that with helge
#we also might want regular conditionals... which I guess will take a native command too... still feels like just writing the lego programmming language but less intuitive...

def process_native_command(command: str, experiment: dict, **kwargs):
    for key, value in kwargs.items():
        print(f"kwargs: {(key, value)}")
    global session, sessionname
    if command == "start":
        # ensure that the directory in which this session should be saved exists
        if not os.path.exists(experiment['meta']['path']):
            os.mkdir(experiment['meta']['path'])
        if not os.path.exists(experiment['meta']['path']) or os.listdir(experiment['meta']['path']) == []:
            session = dict(
                meta=dict(date=datetime.date.today().strftime("%d/%m/%Y")))
            sessionname = f"substrate_{experiment['meta']['substrate']}_session_0"
        # grabs most recent session for this substrate
        if sessionname == None:
            sessionname = highestName(list(filter(
                lambda s: s[-5:] == '.hdf5', os.listdir(experiment['meta']['path']))))[:-5]
            # lazy = False because otherwise it will not load properly
            session = dict(hdfdict.load(os.path.join(
                experiment['meta']['path'], sessionname+'.hdf5'), lazy=False, mode='r+'))
            # if it turns out we need to optimize what is loaded when, we may need to switch packages. Ironically, I am taking the laziest possible approach here to loading and dumping files
        # assigns date to this session if necessary, or replaces session if too old
        if 'date' not in session['meta']:
            session['meta'].update(
                dict(date=datetime.date.today().strftime("%d/%m/%Y")))
        elif session['meta']['date'] != datetime.date.today().strftime("%d/%m/%Y"):
            print(
                'current session is old, saving current session and creating new session')
            hdfdict.dump(session, os.path.join(
                experiment['meta']['path'], sessionname+'.hdf5'), mode='w')
            try:
                print(requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'], 'data', 'uploadhdf5'),
                                   params=dict(filename=sessionname+'.hdf5', filepath=experiment['meta']['path'])).json())
            except:
                print('automatic upload of completed session failed')
            sessionname = incrementName(sessionname)
            session = dict(
                meta=dict(date=datetime.date.today().strftime("%d/%m/%Y")))
        # adds a new run to session to receive incoming data
        if "run_0" not in list(session.keys()):
            session.update(dict(run_0=dict(measurement_no_0={
            }, meta=experiment['params'][experiment['meta']['current_action'].split('/')[1]])))
            run = 0
        else:
            run = incrementName(highestName(
                list(filter(lambda k: k[:4] == "run_", list(session.keys())))))
            session.update({run: dict(measurement_no_0={
            }, meta=experiment['params'][experiment['meta']['current_action'].split('/')[1]])})
            run = int(run[4:])
        # don't put any keys in here that have length less than 4 i guess
        experiment['meta']['run'] = run
        experiment['meta']['measurement_number'] = 0
        session[f"run_{run}"]["measurement_no_0"].update(
            dict(meta=dict(measurement_areas=experiment['meta']['measurement_areas'])))
    elif command == "finish":
        hdfdict.dump(session, os.path.join(
            experiment['meta']['path'], sessionname+'.hdf5'), mode='w')
        print('attempting to upload session')
        try:
            print(requests.get("http://{}:{}/{}/{}".format(config['servers']['dataServer']['host'], config['servers']['dataServer']['port'], 'data', 'uploadhdf5'),
                               params=dict(filename=sessionname+'.hdf5', filepath=experiment['meta']['path'])).json())
        except:
            print('automatic upload of completed session failed')
        hdfdict.dump(dict(meta=dict()), os.path.join(
            experiment['meta']['path'], incrementName(sessionname)+'.hdf5'), mode='w')
        # adds a new hdf5 file which will be used for the next incoming data, thus sealing off the previous one
    elif command == "dummy":
        print("executing 2 second dummy experiment")
        time.sleep(2)
    elif command == "modify":
        # modify undefined parameters of actions further in the experiment
        # worth reiterating that this cannot modify future experiments. the way we have structured everything makes that hard or impossible to do
        # so design things accordingly....
        params = experiment['params']
        vals = kwargs['vals']
        pointers = kwargs['pointers']
        if not isinstance(vals, list):
            vals = [vals]
        if not isinstance(pointers, list):
            pointers = [pointers]
        for val, pointer in zip(vals, pointers):
            if dict_address(pointer, params) != "?":
                raise Exception(
                    f"pointer {pointer} is not intended to be written to")
            dict_address_set(pointer, params, val)
        experiment['params'] = params
    else:
        print("error: native command not recognized")
    return experiment


@app.on_event("startup")
async def memory():
    # the current working dictionary, will be saved as hdf5
    global session
    session = None
    # the filename for above hdf5
    global sessionname
    sessionname = None
    global experiment_queue
    experiment_queue = asyncio.Queue()
    global task
    task = asyncio.create_task(infl())
    global loop
    loop = asyncio.get_event_loop()


@app.on_event("shutdown")
def disconnect():
    global task
    task.cancel()
    if session != None:
        print('saving work on session close -- do not exit terminal')
        hdfdict.dump(session, os.path.join(os.path.join(config['orchestrator']['path'], '_'.join(
            sessionname.split('_')[:2])), sessionname+'.hdf5'), mode='w')
        print('work saved')
    else:
        print('empty session -- no work to save')


if __name__ == "__main__":
    uvicorn.run(app, host=config['servers']['orchestrator']
                ['host'], port=config['servers']['orchestrator']['port'])
