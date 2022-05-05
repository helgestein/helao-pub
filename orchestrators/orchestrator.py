# In order to run the orchestrator, which is at the highest level of Helao, all servers should be started. 
import requests
import sys
import os
from pathlib import Path
import time
import json
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel,validator
from typing import Union,Optional
import numpy
import h5py
import datetime
from copy import copy
import asyncio
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
from util import *
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

##list of changes that i would like to do...
##data management
##then machine learning interface, which hangs on the former
##and mid-run data harvesting, which also hangs on it
##improved input sanitization and proper response codes and request bodies
##improved actions/drivers -- capacity to interface with multiple requests, and mid-action cancelation where possible
##improved interface -- detailed real-time visualization and manipulation of current orchestrator state without command line

#validation for experiment dicts
class Experiment(BaseModel):
    soe: list
    params: dict
    meta: Optional[dict]

    @validator('soe')
    def native_command_ordering(cls,v):
        for i in v:
            if i.count('_') > 1:
                raise ValueError("too many underscores in function name")
        parsed_v = [i.split('_')[0] for i in v]
        if parsed_v.count("orchestrator/start") > 1:
            raise ValueError("cannot have multiple calls to orchestrator/start in single soe")
        if "orchestrator/start" in parsed_v and parsed_v[0] != "orchestrator/start":
            raise ValueError("orchestrator/start must be first action in soe")
        if parsed_v.count("orchestrator/finish") > 1:
            raise ValueError("cannot have multiple calls to orchestrator/finish in single soe")
        if "orchestrator/finish" in parsed_v and parsed_v[-1] != "orchestrator/finish":
            raise ValueError("orchestrator/start must be last action in soe")
        if parsed_v.count("orchestrator/repeat") > 1:
            raise ValueError("cannot have multiple calls to orchestrator/repeat in single soe")    
        if "orchestrator/repeat" in parsed_v and not (parsed_v[-1] == "orchestrator/repeat" or parsed_v[-2] == "orchestrator/repeat" and parsed_v[-1] == "orchestrator/finish"):
            raise ValueError("orchestrator/repeat can only be followed by orchestrator/finish in soe")
        return v

    @validator('params')
    def parameter_correspondence(cls,v,values):
        d = set([i.split('/')[-1] for i in values['soe']])
        if d != set(v.keys()):
            raise ValueError("soe and params are not perfectly corresponding -- must be params entry for every action in soe, and vice-versa")
        if len(d) != len(values['soe']):
            raise ValueError("duplicate entries in soe")
        return v


app = FastAPI(title="orchestrator",
              description="A fancy complex server", version=1.0)


@app.post("/orchestrator/addExperiment")
async def sendMeasurement(experiment: str, thread: int = 0, priority: int = 10):
    global index
    experiment = dict(Experiment(**json.loads(experiment))) # load experiment and run it through pydantic validation
    await scheduler_queue.put((priority,index,experiment,thread))
    index += 1


#receives all experiments, creates new threads, and sends experiments to the appropriate thread
async def scheduler():
    global experiment_queues,experiment_tasks,loop,tracking
    while True:
        priority,index,experiment,thread = await scheduler_queue.get()
        if thread not in experiment_queues.keys(): 
            experiment_queues.update({thread:asyncio.PriorityQueue()})
            experiment_tasks.update({thread:loop.create_task(infl(thread))})
            tracking[thread] = {'path':None,'run':None,'experiment':None,'current_action':None,'status':'uninitialized','history':[]}
        await experiment_queues[thread].put((priority,index,experiment))

#executes a single thread of experiments
async def infl(thread: int):
    while True:
        *_,experiment = await experiment_queues[thread].get()
        if tracking[thread]['status'] == 'clear':
            tracking[thread]['status'] = 'running'
        await doMeasurement(experiment, thread)
        if experiment_queues[thread].empty() and tracking[thread]['status'] == 'running':
            tracking[thread]['status'] = 'clear'

async def doMeasurement(experiment: dict, thread: int):
    global tracking,loop,filelocks,serverlocks,task
    print(f'experiment: {experiment} on thread {thread}')
    if isinstance(tracking[thread]['experiment'],int): # add header for new experiment if you already have an initialized, nonempty experiment
        async with filelocks[tracking[thread]['path']]:
            with h5py.File(tracking[thread]['path'], 'r') as session:
                if len(list(session[f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}"].keys())) > 0:
                    tracking[thread]['experiment'] += 1
    #if 'r' in experiment['meta'].keys() and 'ma' in experiment['meta'].keys(): #calculate measurement areas for meta dict if relevant
    #    experiment['meta'].update(dict(measurement_areas=getCircularMA(experiment['meta']['ma'][0],experiment['meta']['ma'][1],experiment['meta']['r'])))
    experiment['meta']['thread'] = thread #put thread in experiment so that native commands receive it.  
    #handling unset-up threads. couple to the thread directly below if it exists, or raise a flag and skip the experiment if it doesn't
    if experiment['soe'] != [] and all([tracking[thread][i] == None for i in ['path','run','experiment','current_action']]) and experiment['soe'][0].split('_')[0] != 'orchestrator/start':
        print(f"thread {thread} for experiment {experiment} has not been set up")
        if thread-1 in tracking.keys() and all([tracking[thread][i] != None for i in ['path','run','experiment','current_action']]):
            tracking[thread]['path'] = tracking[thread-1]['path']
            tracking[thread]['run'] = tracking[thread-1]['run']
            tracking[thread]['experiment'] = 0
            print(f"thread {thread} bound to thread {thread-1}")
        else:
            experiment = {'soe':[],'params':{},'meta':{}}
            print("experiment has been blanked")

    for action_str in experiment['soe']:
        server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
        while tracking[thread]['status'] != 'running' and server != 'orchestrator':
            await asyncio.sleep(.1)
        tracking[thread]['current_action'] = fnc
        action = fnc.split('_')[0]
        params = experiment['params'][fnc]
        servertype = server.split(':')[0]
        if server not in serverlocks.keys() and servertype != "orchestrator":
            serverlocks[server] = asyncio.Lock()

        #"if servertype != 'orchestrator':" is a placeholder for the appropriate conditional. need to decide how or whether we will label different types of servers
        if servertype != 'orchestrator': #server is normal
            while True:
                async with serverlocks[server]:
                    res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/{action}")
                if 200 <= res.status_code < 300: #ensure that action completed successfully
                    res = res.json()
                    break
                else: #alert the user if action did not complete successfully, and pause until they say problem is fixed.
                    print(f"Orchestrator has received an invalid response attempting action {action_str} with parameters {params}.")
                    input('Fix the problem, and press Enter to try the action again.')
        elif servertype == '': #server needs data from ongoing series of experiments
            pass
        elif servertype == 'orchestrator':
            if params == None:
                params = {}
            #orchestrator should be allowed to crash if it fails on a native command, as continuing to the next experiment could put it in an unsafe state.
            #or maybe i just want to clear thread or something. leaving this for now.
            experiment = await process_native_command(action,experiment,**params)
            continue

        #look at this with Fuzhan. objectives are firstly to make this code simpler, more readable, and more generalized (easy) 
        # and secondly to make the scripting needed to properly use it easier (hard)
        elif servertype == 'analysis':
            add = list(filter(lambda s: s.split('_')[-1] == 'address',params.keys()))
            if add != []: #be sure to use these parameter names "foo_address" in action if (and only if?) you are loading from ongoing sessions. must be string hdf5 paths
                t = int(params[add[0]].split('/')[0].split(':')[1]) #assuming all addresses come from same file
                if tracking[t]['path'] != None:
                    async with filelocks[tracking[t]['path']]:
                        await loop.run_in_executor(None,lambda x: requests.get(x,params=dict(path=tracking[t]['path'],run=tracking[t]['run'],addresses=json.dumps({a:params[a] for a in add}))),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/receiveData")
                else:
                    for h in tracking[thread]['history']:
                        async with filelocks[h['path']]:
                            if paths_in_hdf5(h['path'],[params[a] for a in add]):
                                await loop.run_in_executor(None,lambda x: requests.get(x,params=dict(path=h['path'],run=h['run'],addresses=json.dumps({a:params[a] for a in add}))),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/receiveData")
                                break
            async with serverlocks[server]:
                res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/{action}")
        elif servertype == 'ml':
            if "address" in params.keys():
                #be sure to use this parameter name "address" in action if (and only if?) you are loading from ongoing session. must be string hdf5 path
                t = int(params['address'].split('/')[0].split(':')[1])
                if tracking[t]['path'] != None:
                    async with serverlocks[server]:
                        async with filelocks[tracking[t]['path']]:
                            if 'modelid' in params.keys():
                                await loop.run_in_executor(None,lambda x: requests.get(x,params=dict(path=tracking[t]['path'],run=tracking[t]['run'],address=params['address'],modelid=params['modelid'])),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/receiveData")
                            else:
                                await loop.run_in_executor(None,lambda x: requests.get(x,params=dict(path=tracking[t]['path'],run=tracking[t]['run'],address=params['address'])),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/receiveData")
                else:
                    for h in tracking[thread]['history']:
                        async with serverlocks[server]:
                            async with filelocks[h['path']]:
                                if paths_in_hdf5(h['path'],params['address']):
                                    if 'modelid' in params.keys():
                                        await loop.run_in_executor(None,lambda x: requests.get(x,params=dict(path=h['path'],run=h['run'],address=params['address'],modelid=params['modelid'])),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/receiveData")
                                    else:
                                        await loop.run_in_executor(None,lambda x: requests.get(x,params=dict(path=h['path'],run=h['run'],address=params['address'])),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/receiveData")
                                    break
            async with serverlocks[server]:
                res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/{action}")
        
        async with filelocks[tracking[thread]['path']]:
            res.update({'meta':{'measurement_time':datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}})
            save_dict_to_hdf5({fnc:res},tracking[thread]['path'],path=f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}/",mode='a')
            with h5py.File(tracking[thread]['path'], 'r') as session: #add metadata to experiment
                l = list(session[f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}"].keys())
                if len(l) > 0 and 'meta' not in l: #disregard if you did not do any real actions this experiment, or if meta already added
                    session.close()
                    save_dict_to_hdf5({'meta':experiment['meta']},tracking[thread]['path'],path=f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}/",mode='a')
        print(f"function {fnc} in thread {thread} completed at {time.time()}")
        print(f"function operating in run {tracking[thread]['run']} in file {tracking[thread]['path']}")

async def process_native_command(command: str,experiment: dict,**params):
    if command in ['start','finish','modify','wait','repeat']:
        return await getattr(sys.modules[__name__],command)(experiment,**params)
    else:
        raise Exception("native command not recognized")

#ensure appropriate folder, file, and all keys and tracking variables are appropriately initialized at the beginning of a run
#params:
#   collectionkey: string, determines folder and file names for session, may correspond to key of experiment['meta'], in which case name will be indexed by that value.
#   meta: dict, will be placed as metadata under the header of the run set up by this command
async def start(experiment: dict,collectionkey:str,meta:dict={}):
    global tracking,filelocks,serverlocks
    thread = experiment['meta']['thread']
    if collectionkey in experiment['meta'].keys():#give the directory an index if one is provided
        h5dir = os.path.join(config[serverkey]['path'],f"{collectionkey}_{experiment['meta'][collectionkey]}")
    else:#or a name without an index if not.
        h5dir = os.path.join(config[serverkey]['path'],f"{collectionkey}")
    h5dirlist = str(Path(h5dir)).split('\\') #ensure that the directory in which this session should be saved exists
    for folder in ['\\'.join(h5dirlist[:i+1]) for f,i in zip(h5dirlist,range(len(h5dirlist)))]:
        if not os.path.exists(folder):
            os.mkdir(folder)

    if list(filter(lambda s: s[-3:]=='.h5',os.listdir(h5dir))) == []: #if no current session to load, create a session
        tracking[thread]['path'] = os.path.join(h5dir,config['instrument']+'_'+os.path.basename(h5dir)+'_session_0.h5')
        if tracking[thread]['path'] not in filelocks.keys(): #add a lock to a file if it does not already exist
            filelocks[tracking[thread]['path']] = asyncio.Lock()
        async with filelocks[tracking[thread]['path']]:
            save_dict_to_hdf5(dict(meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))),tracking[thread]['path'])
    
    else: #otherwise grab most recent session in dir
        tracking[thread]['path'] = os.path.join(h5dir,highestName(list(filter(lambda s: s[-3:]=='.h5',os.listdir(h5dir)))))
        if tracking[thread]['path'] not in filelocks.keys():
            filelocks[tracking[thread]['path']] = asyncio.Lock()
    async with filelocks[tracking[thread]['path']]:
        with h5py.File(tracking[thread]['path'], 'r') as session: ###i don't love the old replacement thing, let's brainstorm something better
            if 'date' not in session['meta'].keys(): #assigns date to this session if necessary, or replaces session if too old
                session.close()
                save_dict_to_hdf5(dict(date=datetime.date.today().strftime("%d/%m/%Y")),tracking[thread]['path'],path='/meta/',mode='a')
            elif session['meta/date/'][()] != datetime.date.today().strftime("%d/%m/%Y"):
                print('current session is old, saving current session and creating new session')
                session.close()
                if "orch_kadi" not in serverlocks.keys():
                    serverlocks["orch_kadi"] = asyncio.Lock()
                try:
                    async with serverlocks["orch_kadi"]:
                        print(requests.get(f"{config[serverkey]['kadiurl']}/kadi/uploadhdf5",
                            params=dict(filename=os.path.basename(tracking[thread]['path']),filepath=os.path.dirname(tracking[thread]['path']))).json())
                except:
                    print('automatic upload of completed session failed')
                tracking[thread]['path'] = os.path.join(h5dir,incrementName(os.path.basename(tracking[thread]['path'])))
                if tracking[thread]['path'] not in filelocks.keys():
                    filelocks[tracking[thread]['path']] = asyncio.Lock()
                async with filelocks[tracking[thread]['path']]:
                    save_dict_to_hdf5(dict(meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))),tracking[thread]['path'])
    
    async with filelocks[tracking[thread]['path']]:
        with h5py.File(tracking[thread]['path'], 'r') as session: #adds a new run to session to receive incoming data
            if "run_0" not in session.keys(): 
                session.close()
                save_dict_to_hdf5({"run_0":{f"experiment_0:{thread}":None},"meta":meta},tracking[thread]['path'],mode='a')
                tracking[thread]['run'] = 0
            else:
                run = incrementName(highestName(list(filter(lambda k: k[:4]=="run_",list(session.keys()))))) #don't put any keys in here that have length less than 4 i guess
                session.close()
                save_dict_to_hdf5({run:{f"experiment_0:{thread}":None,"meta":meta}},tracking[thread]['path'],mode='a')
                tracking[thread]['run'] = int(run[4:])
        tracking[thread]['experiment'] = 0
        save_dict_to_hdf5({'meta':None},tracking[thread]['path'],path=f'/run_{tracking[thread]["run"]}/experiment_0:{thread}/',mode='a')
    tracking[thread]['status'] = 'running'
    return experiment

#ensure tracking variables are appropriately reset at the end of a run, and upload finished session
#params:
#   none
async def finish(experiment: dict):
    global tracking,filelocks,serverlocks
    thread = experiment['meta']['thread']
    print(f'thread {thread} finishing')
    l = sum([1 if tracking[k]['path'] == tracking[thread]['path'] else 0 for k in tracking.keys()]) #how many threads are currently working on this file?
    if l == 1: #if this is the last thread working on the file, upload file
        print('attempting to upload session')
        if "orch_kadi" not in serverlocks.keys():
            serverlocks["orch_kadi"] = asyncio.Lock()
        try:
            async with serverlocks["orch_kadi"]:
                print(requests.get(f"{config[serverkey]['kadiurl']}/kadi/uploadhdf5",
                    params=dict(filename=os.path.basename(tracking[thread]['path']),filepath=os.path.dirname(tracking[thread]['path']))).json())
        except:
            print('automatic upload of completed session failed')

        #adds a new hdf5 file which will be used for the next incoming data, thus sealing off the previous one
        newpath = os.path.join(os.path.dirname(tracking[thread]['path']),incrementName(os.path.basename(tracking[thread]['path'])))
        filelocks[newpath] = asyncio.Lock()
        async with filelocks[tracking[thread]['path']]:
            save_dict_to_hdf5(dict(meta=None),newpath)

        #clear history relating to this file from all threads
        for t in tracking.values():
            for h in t['history']:
                if h['path'] == tracking['thread']['path']:
                    del h
    else:
        print(f'{l-1} threads still operating on {tracking[thread]["path"]}')
        #free up the thread
        tracking[thread] = {'path':None,'run':None,'experiment':None,'current_action':None,'status':'uninitialized','history':[{'path':tracking[thread]['path'],'run':tracking[thread]['run']}]+tracking[thread]['history']}
    return experiment


#set undefined values under experiment parameter dict
#values must come from currently running threads
#params:
#   addresses: within a run, address(es) of the value(s) that should be transmitted to parameter(s)
#   pointers: within param dict of experiment, addresses to transmit values to. parameter must have previously been initialized as "?"
async def modify(experiment: dict,addresses:Union[str,list],pointers:Union[str,list]):
    global tracking,filelocks
    mainthread = experiment['meta']['thread']
    if not isinstance(addresses, list):
        addresses = [addresses]
    if not isinstance(pointers, list):
        pointers = [pointers]
    assert len(addresses) == len(pointers)
    threads = [int(address.split('/')[0].split(':')[1]) for address in addresses]
    for address, pointer, thread in zip(addresses, pointers, threads):
        if dict_address(pointer, experiment['params']) != "?":
            raise Exception(f"pointer {pointer} is not intended to be written to")
        if tracking[thread]['path'] != None:
            async with filelocks[tracking[thread]['path']]:
                with h5py.File(tracking[thread]['path'], 'r') as session:
                    val = session[f'run_{tracking[thread]["run"]}/'+address][()]
                    dict_address_set(pointer, experiment['params'],val)
                    print(f'pointer {pointer} in params for experiment {tracking[mainthread]["experiment"]} in thread {mainthread} set to {val}')
        else:
            for h in tracking[thread]['history']:
                if h['path'] == tracking[thread]['path']:
                    async with filelocks[h['path']]:
                        with h5py.File(h['path'], 'r') as session:
                            try:
                                val = session[f'run_{h["run"]}/'+address][()]
                            except:
                                continue
                            dict_address_set(pointer, experiment['params'],val)
                            print(f'pointer {pointer} in params for experiment {tracking[mainthread]["experiment"]} in thread {mainthread} set to {val} from history')
                            break
            if dict_address(pointer,experiment['params']) == '?':
                raise Exception('modify failed to find address in history')
    return experiment


#pause experiment until given thread(s) complete(s) given action(s)
#params:
#   	addresses: path(s) below run to awaited address(es)
#
#address should generally be 2 keys deep, with the format "experiment/action". might have problems if this is not the case
async def wait(experiment: dict, addresses: Union[str,list]):
    global tracking,filelocks
    print(f"waiting on {addresses}")
    if not isinstance(addresses, list):
        addresses = [addresses]
    threads = [int(address.split('/')[0].split(':')[1]) for address in addresses]
    while addresses != []:
        await asyncio.sleep(.1) # give other processes a chance to look at the file...
        c = list(zip(range(len(addresses)),copy(addresses), copy(threads)))
        for i,address,thread in c:
            if tracking[thread]['path'] != None:
                async with filelocks[tracking[thread]['path']]:
                    with h5py.File(tracking[thread]['path'], 'r') as session:
                        exp = address.split('/')[0]
                        action = address.split('/')[1]
                        if exp in session[f'run_{tracking[thread]["run"]}/'].keys():
                            if action in session[f'run_{tracking[thread]["run"]}/{exp}'].keys():
                                print(f"{addresses[i]} found")
                                del addresses[i]
                                del threads[i]
                                break#If multiple addresses are found in the same for loop, 'i' will no longer map to the correct index of addresses/threads
            else:#if you are waiting on the results of a session that already finished, check history for path and run
                for h in tracking[thread]['history']:
                    if h['path'] == tracking[thread]['path']:
                        async with filelocks[h['path']]:
                            with h5py.File(h['path'], 'r') as session:
                                exp = address.split('/')[0]
                                action = address.split('/')[1]
                                if exp in session[f'run_{h["run"]}/'].keys():
                                    if action in session[f'run_{h["run"]}/{exp}'].keys():
                                        print(f"{addresses[i]} found in history")
                                        del addresses[i]
                                        del threads[i]
    return experiment

#submit an experiment identical to the current one to the orchestrator thread.
#will have higher-than default priority, and so will go before any intervening experiments that may have been submitted.
#an experiment should only have one call of repeat, and it should only be at the end of the experiment (unless followed by a finish command)
#params:
#        n: number of times to repeat after 1st experiment, or 0 to repeat until forced to stop
#if i could get a version of repeat that changes the parameters slightly each time, i would rule the world
# aka make scripting in the orchestrator much simpler
async def repeat(experiment: dict, n: int = 0, priority: int = 5):
    global index
    #copy current experiment
    new_exp = experiment
    if n == 1: #if n=1, repeating is finished.
        del new_exp['params']['repeat']
        del new_exp['soe'][-1]
    elif n != 0: #else, decrement repeats left to go
        new_exp['params']['repeat'] -= 1
    #and of course, for n==0, we do nothing and it repeats forever
    #then the new experiment is added to the appropriate queue with a higher-than-default priority
    await experiment_queues[experiment['meta']['thread']].put((priority,index,new_exp))
    index += 1
    return experiment

@app.on_event("startup")
async def memory():
    global tracking
    tracking = {} #a dict of useful variables to keep track of
    global scheduler_queue
    scheduler_queue = asyncio.PriorityQueue()
    global task
    task = asyncio.create_task(scheduler())
    
    global experiment_queues
    experiment_queues = {}
    global experiment_tasks
    experiment_tasks = {}

    global filelocks
    filelocks = {}
    global serverlocks
    serverlocks = {}

    global loop
    loop = asyncio.get_event_loop()
    global error
    error = loop.create_task(raise_exceptions())
    
    global index #assign a number to each experiment to retain order within priority queues
    index = 0


@app.on_event("shutdown")
def disconnect():
    global task, error
    if not error.cancelled():
        error.cancel()
    if not task.cancelled():
        task.cancel()
    for t in experiment_tasks.values():
        if not t.cancelled():
            t.cancel()


#empty queue for thread, or for all threads if no thread specified.
@app.post("/orchestrator/clear")
def clear(thread: Optional[int] = None):
    global experiment_queues
    if thread == None:
        for k in experiment_queues.keys():
            while not experiment_queues[k].empty():
                experiment_queues[k].get_nowait()
    elif thread in experiment_queues.keys():
        while not experiment_queues[thread].empty():
            experiment_queues[thread].get_nowait()
    else:
        print(f"thread {thread} not found")

#empty queue and cancel current experiment for thread, or for all threads if no thread specified.
@app.post("/orchestrator/kill")
def kill(thread: Optional[int] = None):
    global experiment_tasks,tracking
    clear(thread)
    if thread == None:
        for k in experiment_tasks.keys():
            experiment_tasks[k].cancel()
            del experiment_tasks[k]
            experiment_tasks.update({k:loop.create_task(infl(k))})
            h = {'path':tracking[k]['path'],'run':tracking[k]['run']}
            tracking[k] = {'path':None,'run':None,'experiment':None,'current_action':None,'status':'uninitialized','history':[h]+tracking[k]['history']}
    elif thread in experiment_tasks.keys():
        experiment_tasks[thread].cancel()
        del experiment_tasks[thread]
        experiment_tasks.update({thread:loop.create_task(infl(thread))})
        h = {'path':tracking[thread]['path'],'run':tracking[thread]['run']}
        tracking[thread] = {'path':None,'run':None,'experiment':None,'current_action':None,'status':'uninitialized','history':[h]+tracking[thread]['history']}
    else:
        print(f"thread {thread} not found")


@app.post("/orchestrator/pause")
def pause(thread: Optional[int] = None):
    global tracking
    if thread == None:
        for k in tracking.keys():
            if tracking[k]['status'] == 'running':
                tracking[k]['status'] = 'paused'
                print(f"thread {k} paused")
            else:
                print(f'attempted to pause thread {k}, but status was {tracking[k]["status"]}')
    elif thread in tracking.keys():
        if tracking[thread]['status'] == 'running':
                tracking[thread]['status'] = 'paused'
                print(f"thread {thread} paused")
        else:
            print(f'attempted to pause thread {thread}, but status was {tracking[thread]["status"]}')
    else:
        print(f"thread {thread} not found")


@app.post("/orchestrator/resume")
def resume(thread: Optional[int] = None):
    global tracking
    if thread == None:
        for k in tracking.keys():
            if tracking[k]['status'] == 'paused':
                tracking[k]['status'] = 'running'
                print(f"thread {k} resumed")
            else:
                print(f'attempted to resume thread {k}, but status was {tracking[k]["status"]}')
    elif thread in tracking.keys():
        if tracking[thread]['status'] == 'paused':
                tracking[thread]['status'] = 'running'
                print(f"thread {thread} resumed")
        else:
            print(f'attempted to resume thread {thread}, but status was {tracking[thread]["status"]}')
    else:
        print(f"thread {thread} not found")


@app.post("/orchestrator/getStatus")
def get_status():
    return tracking


# error handing within the infinite loop
# check for exceptions. if found, print stack trace and cancel infinite loop
async def raise_exceptions():
    global task,experiment_tasks,error
    while True:
        # check for errors every second (maybe this should be a different number?)
        await asyncio.sleep(1)
        try:
            task.exception()
            task.print_stack()
            break
        except:
            pass
        tf = None
        for t in experiment_tasks.values():
            try:
                t.exception()
                t.print_stack()
                tf = t
                break
            except:
                pass
        try:
            tf.exception()
            break
        except:
            pass
    #if an error shows up anywhere, bring the whole house down.
    for k in experiment_tasks.values():
        try:
            k.cancel()
        except:
            pass
    try:
        task.cancel()
    except:
        pass
    try:
        error.cancel()
    except:
        pass

###this function is not very good, and the whole feature will be done more rigorously when we revisit data management.
#send data from a currently running series of experiments to the requesting entity
@app.get("/orchestrator/getData")
#addresses are assumed to hit under each experiment
#thread will use currently iterating or last iterating run
#options we should have: list mode, get next, group mode
async def getData(thread:int,addresses:str,mode:str,wait:float=.01):
    await asyncio.sleep(wait)#silly expedient so this doesn't block and gets the right experiment
    data = []
    try:
        addresses = json.loads(addresses)
    except:
        addresses = [addresses]
    if mode not in ['list','group','next']:
        raise ValueError('invalid mode for getData')
    path = tracking[thread]['path'] if tracking[thread]['path'] != None else tracking[thread]['history'][0]['path']
    run = tracking[thread]['run'] if tracking[thread]['path'] != None else tracking[thread]['history'][0]['run']
    if mode == 'list':
        async with filelocks[path]:
            with h5py.File(path, 'r') as session:
                experiments = list(session[f'run_{run}'].keys())
                for experiment in experiments:
                    subdata = []
                    for address in addresses:
                        dpath = f'run_{run}/'+experiment+'/'+address
                        if paths_in_hdf5(session,dpath):
                            datum = hdf5_group_to_dict(session,dpath)
                            if isinstance(datum,numpy.ndarray):
                                datum = datum.tolist()
                            subdata.append(datum)
                        else:
                            print(f'address {address} not found in file')    
                    if subdata != []:
                        data.append(subdata if len(subdata) != 1 else subdata[0])
    elif mode == 'group':
        async with filelocks[path]:
            with h5py.File(path, 'r') as session:
                for address in addresses:
                    data.append(hdf5_group_to_dict(session,f'run_{run}/{address}'))
    elif mode == 'next':
        new_exp = f'experiment_{tracking[thread]["experiment"]}:{thread}'
        print(f'awaiting data at {new_exp}')
        present = False
        while not present:
            async with filelocks[path]:
                with h5py.File(path, 'r') as session:
                    present = paths_in_hdf5(path,[f'run_{run}/{new_exp}/{address}' for address in addresses])
                await asyncio.sleep(.1)
        for address in addresses:
            async with filelocks[path]:
                with h5py.File(path, 'r') as session:
                    datum = hdf5_group_to_dict(session,f'run_{run}/{new_exp}/{address}')
            if isinstance(datum,numpy.ndarray):
                datum = datum.tolist()
            data.append(datum)
    return data


if __name__ == "__main__":
    uvicorn.run(app, host= config['servers'][serverkey]['host'], port= config['servers'][serverkey]['port'])

