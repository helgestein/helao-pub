# In order to run the orchestrator, which is at the highest level of Helao, all servers should be started. 
import requests
import sys
import os
import time
from fastapi import FastAPI,BackgroundTasks
from pydantic import BaseModel
import json
import uvicorn
from fastapi import FastAPI, Query
import json
import h5py
import datetime
from copy import copy
import asyncio
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
sys.path.append(os.path.join(helao_root, 'config'))
from util import *
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title = "orchestrator", description = "A fancy complex server",version = 1.0)



@app.post("/orchestrator/addExperiment")
async def sendMeasurement(experiment: str, thread: int = 0):
    await scheduler_queue.put((experiment,thread))

#receives all experiments, creates new threads, and sends experiments to the appropriate thread
async def scheduler():
    global experiment_queues,experiment_tasks,loop,tracking
    while True:
        experiment,thread = await scheduler_queue.get()
        if thread not in experiment_queues.keys(): 
            experiment_queues.update({thread:asyncio.Queue()})
            experiment_tasks.update({thread:loop.create_task(infl(thread))})
            tracking[thread] = {'path':None,'run':None,'experiment':None,'current_action':None,'history':[]}
        await experiment_queues[thread].put(experiment)

async def infl(thread):
    while True:
        experiment = await experiment_queues[thread].get()
        await doMeasurement(experiment, thread)

async def doMeasurement(experiment: str, thread: int):
    global tracking,loop,locks
    print('experiment: '+experiment)
    experiment = json.loads(experiment) # load experiment
    if isinstance(tracking[thread]['experiment'],int): # add header for new experiment if you already have an initialized, nonempty experiment
        async with locks[tracking[thread]['path']]:
            with h5py.File(tracking[thread]['path'], 'r') as session:
                if len(list(session[f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}"].keys())) > 0:
                    tracking[thread]['experiment'] += 1
    if 'r' in experiment['meta'].keys() and 'ma' in experiment['meta'].keys(): #calculate measurement areas for meta dict if relevant
        experiment['meta'].update(dict(measurement_areas=getCircularMA(experiment['meta']['ma'][0],experiment['meta']['ma'][1],experiment['meta']['r'])))
    experiment['meta']['thread'] = thread #put thread in experiment so that native commands receive it.
    if {k:v for k,v in tracking[thread].items() if k != 'history'} == {'path':None,'run':None,'experiment':None,'current_action':None} and experiment['soe'][0].split('_')[0] != 'orchestrator/start':
        tracking[thread]['path'] = tracking[thread-1]['path'] #set up tracking here if no start command
        tracking[thread]['run'] = tracking[thread-1]['run']
        tracking[thread]['experiment'] = 0
    for action_str in experiment['soe']:
        server, fnc = action_str.split('/') #Beispiel: action: 'movement' und fnc : 'moveToHome_0
        tracking[thread]['current_action'] = fnc
        action = fnc.split('_')[0]
        params = experiment['params'][fnc]
        servertype = server.split(':')[0]
        if servertype in ['movement','motor','pumping','minipumping','echem','forceAction','table','oceanAction','ocean','owis','arcoptix','dummy']:
            res = await loop.run_in_executor(None,lambda x: requests.get(x,params=params).json(),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/{action}")
        elif servertype == 'data':
            await loop.run_in_executor(None,lambda x: requests.get(x,params=params),f"http://{config['servers'][server]['host']}:{config['servers'][server]['port']}/{servertype}/{action}")
            continue
        elif servertype == 'orchestrator':
            if params == None:
                params = {}
            experiment = await process_native_command(action,experiment,**params)
            #loop.run_in_executor(None,lambda c,e: process_native_command(c,e,**params),action,experiment)
            continue
        elif servertype == 'analysis':
            continue
        elif servertype == 'learning':
            continue
        async with locks[tracking[thread]['path']]:
            save_dict_to_hdf5({fnc:{'data':res,'measurement_time':datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")}},tracking[thread]['path'],path=f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}/",mode='a')
            with h5py.File(tracking[thread]['path'], 'r') as session: #add metadata to experiment
                l = list(session[f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}"].keys())
                if len(l) > 0 and 'meta' not in l: #disregard if you did not do any real actions this experiment, or if meta already added
                    session.close()
                    save_dict_to_hdf5({'meta':experiment['meta']},tracking[thread]['path'],path=f"/run_{tracking[thread]['run']}/experiment_{tracking[thread]['experiment']}:{thread}/",mode='a')

async def process_native_command(command: str,experiment: dict,**params):
    if command in ['start','finish','modify','wait']:
        return await getattr(sys.modules[__name__],command)(experiment,**params)
    else:
        raise Exception("native command not recognized")

#ensure appropriate folder, file, and all keys and tracking variables are appropriately initialized at the beginning of a run
#params:
#   collectionkey: string, determines folder and file names for session, may correspond to key of experiment['meta'], in which case name will be indexed by that value.
#   meta: dict, will be placed as metadata under the header of the run set up by this command
async def start(experiment: dict,collectionkey:str,meta:dict={}):
    global tracking,locks
    thread = experiment['meta']['thread']
    if collectionkey in experiment['meta'].keys():#give the directory an index if one is provided
        h5dir = os.path.join(config[serverkey]['path'],f"{collectionkey}_{experiment['meta'][collectionkey]}")
    else:#or a name without an index if not.
        h5dir = os.path.join(config[serverkey]['path'],f"{collectionkey}")
    if not os.path.exists(h5dir): #ensure that the directory in which this session should be saved exists
        os.mkdir(h5dir)
    if os.listdir(h5dir) == []: #if dir is empty, create a session
        tracking[thread]['path'] = os.path.join(h5dir,config['instrument']+'_'+os.path.basename(h5dir)+'_session_0.hdf5')
        if tracking[thread]['path'] not in locks.keys(): #add a lock to a file if it does not already exist
            locks[tracking[thread]['path']] = asyncio.Lock()
        async with locks[tracking[thread]['path']]:
            save_dict_to_hdf5(dict(meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))),tracking[thread]['path'])
    else: #otherwise grab most recent session in dir
        tracking[thread]['path'] = os.path.join(h5dir,highestName(list(filter(lambda s: s[-5:]=='.hdf5',os.listdir(h5dir)))))
        if tracking[thread]['path'] not in locks.keys():
            locks[tracking[thread]['path']] = asyncio.Lock()
    async with locks[tracking[thread]['path']]:
        with h5py.File(tracking[thread]['path'], 'r') as session:
            if 'date' not in session['meta'].keys(): #assigns date to this session if necessary, or replaces session if too old
                session.close()
                save_dict_to_hdf5(dict(date=datetime.date.today().strftime("%d/%m/%Y")),tracking[thread]['path'],path='/meta/',mode='a')
            elif session['meta/date/'][()] != datetime.date.today().strftime("%d/%m/%Y"):
                print('current session is old, saving current session and creating new session')
                session.close()
                try:
                    print(requests.get(f"{config[serverkey]['kadiurl']['host']}/{'data'}/uploadhdf5",
                        params=dict(filename=os.path.basename(tracking[thread]['path']),filepath=os.path.dirname(tracking[thread]['path']))).json())
                except:
                    print('automatic upload of completed session failed')
                tracking[thread]['path'] = os.path.join(h5dir,incrementName(os.path.basename(tracking[thread]['path'])))
                if tracking[thread]['path'] not in locks.keys():
                    locks[tracking[thread]['path']] = asyncio.Lock()
                async with locks[tracking[thread]['path']]:
                    save_dict_to_hdf5(dict(meta=dict(date=datetime.date.today().strftime("%d/%m/%Y"))),tracking[thread]['path'])
    async with locks[tracking[thread]['path']]:
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
    return experiment

#ensure tracking variables are appropriately reset at the end of a run, and upload finished session
#params:
#   none
async def finish(experiment: dict):
    global tracking,locks
    thread = experiment['meta']['thread']
    print(f'thread {thread} finishing')
    l = sum([1 if tracking[k]['path'] == tracking[thread]['path'] else 0 for k in tracking.keys()]) #how many threads are currently working on this file?
    if l == 1: #if this is the last thread working on the file, upload file
        print('attempting to upload session')
        try:
            print(requests.get(f"{config[serverkey]['kadiurl']['host']}/{'data'}/uploadhdf5",
                        params=dict(filename=os.path.basename(tracking[thread]['path']),filepath=os.path.dirname(tracking[thread]['path']))).json())
        except:
            print('automatic upload of completed session failed')
        tracking[thread]['path'] = os.path.join(os.path.dirname(tracking[thread]['path']),incrementName(os.path.basename(tracking[thread]['path'])))
        locks[tracking[thread]['path']] = asyncio.Lock()
        async with locks[tracking[thread]['path']]:
            save_dict_to_hdf5(dict(meta=None),tracking[thread]['path'])
        #adds a new hdf5 file which will be used for the next incoming data, thus sealing off the previous one
    else:
        print(f'{l-1} threads still operating on {tracking[thread]["path"]}')
    #free up the thread
    tracking[thread] = {'path':None,'run':None,'experiment':None,'current_action':None,'history':[{'path':tracking[thread]['path'],'run':tracking[thread]['run']}]+tracking[thread]['history']}
    return experiment
    
#set undefined values under experiment parameter dict
#values must come from currently running threads
#params:
#   addresses: within a run, address(es) of the value(s) that should be transmitted to parameter(s)
#   pointers: within param dict of experiment, addresses to transmit values to. parameter must have previously been initialized as "?"
async def modify(experiment: dict,addresses,pointers):
    global tracking,locks
    mainthread = experiment['meta']['thread']
    if not isinstance(addresses, list):
        addresses = [addresses]
    if not isinstance(pointers, list):
        pointers = [pointers]
    threads = [int(address.split('/')[0].split(':')[-1]) for address in addresses]
    for address, pointer, thread in zip(addresses, pointers, threads):
        if dict_address(pointer, experiment['params']) != "?":
            raise Exception(f"pointer {pointer} is not intended to be written to")
        if tracking[thread]['path'] != None:
            async with locks[tracking[thread]['path']]:
                with h5py.File(tracking[thread]['path'], 'r') as session:
                    val = session[f'run_{tracking[thread]["run"]}/'+address][()]
                    dict_address_set(pointer, experiment['params'],val)
                    print(f'pointer {pointer} in params for experiment {tracking[mainthread]["experiment"]} in thread {mainthread} set to {val}')
        else:
            for h in tracking[thread]['history']:
                async with locks[h['path']]:
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
async def wait(experiment: dict,addresses):
    global tracking,locks
    print(f"waiting on {addresses}")
    if not isinstance(addresses, list):
        addresses = [addresses]
    threads = [int(address.split('/')[0].split(':')[-1]) for address in addresses]
    while addresses != []:
        await asyncio.sleep(1) # give other processes a chance to look at the file...
        c = list(zip(range(len(addresses)),copy(addresses), copy(threads)))
        for i,address,thread in c:
            if tracking[thread]['path'] != None:
                async with locks[tracking[thread]['path']]:
                    with h5py.File(tracking[thread]['path'], 'r') as session:
                        exp = address.split('/')[0]
                        action = address.split('/')[1]
                        if exp in session[f'run_{tracking[thread]["run"]}/'].keys():
                            if action in session[f'run_{tracking[thread]["run"]}/{exp}'].keys():
                                print(f"{addresses[i]} found")
                                del addresses[i]
                                del threads[i]
            else:#if you are waiting on the results of a session that already finished, check history for path and run
                for h in tracking[thread]['history']:
                    async with locks[h['path']]:
                        with h5py.File(h['path'], 'r') as session:
                            exp = address.split('/')[0]
                            action = address.split('/')[1]
                            if exp in session[f'run_{h["run"]}/'].keys():
                                if action in session[f'run_{h["run"]}/{exp}'].keys():
                                    print(f"{addresses[i]} found in history")
                                    del addresses[i]
                                    del threads[i]
                                    break
    return experiment

@app.on_event("startup")
async def memory():
    global tracking
    tracking = {} #a dict of useful variables to keep track of
    global scheduler_queue
    scheduler_queue = asyncio.Queue()
    global task
    task = asyncio.create_task(scheduler())
    
    global experiment_queues
    experiment_queues = {}
    global experiment_tasks
    experiment_tasks = {}

    global locks
    locks = {}

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
    for t in experiment_tasks.values():
        if not t.cancelled():
            t.cancel()

#error handing within the infinite loop
#check for exceptions. if found, print stack trace and cancel infinite loop 
async def raise_exceptions():
    global task,experiment_tasks,error
    while True:
        await asyncio.sleep(1) #check for errors every second (maybe this should be a different number?)
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
    for k in experiment_tasks.values():#if an error shows up anywhere, bring the whole house down.
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




if __name__ == "__main__":
    uvicorn.run(app, host= config['servers'][serverkey]['host'], port= config['servers'][serverkey]['port'])