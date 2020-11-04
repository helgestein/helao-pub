import sys
import os
import json
import time
import requests
import asyncio
import aiohttp
from importlib import import_module

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify
from collections import deque

# not packaging as module for now, so detect source code's root directory from CLI execution
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# append config folder to path to allow dynamic config imports
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
from core import OrchHandler
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

"""
TODO: every action/instrument server gets /ws_data and /ws_status websockets, /get_status endpoint, /abort endpoint
TODO: action/isntrument server has coroutine which listens for /abort
TODO: gamry abort will end measurement, galil_motion will stop motors, galil_io will turn off outputs
TODO: orchestrator also gets /status websocket, /get_status endpoint, /abort endpoint
TODO: orchestrator has coroutine which listens for /abort
TODO: orchestrator has 1) list of decisions to process; 2) queue of actions for a given decision
TODO: orchestrator /abort will terminate queue and pause list execution
TODO: orchestrator assigns decision provenance to all actions in queue; action servers receive provenance and save metadata
TODO: orchestrator has coroutine that listens to all FastAPI action servers and updates global state dict "STATES"

TODO: queue dispatcher
0. OrchServ has an asyncio queue for receiving status messages from / ws / endpoint ActServ
1. check ORCH status for blocking flag
2. if blocking, await ORCH queue
"""


# TESTING
import os, sys, json, requests, asyncio, websockets
from importlib import import_module
from munch import munchify

sys.path.append(os.path.join(os.getcwd(), 'config'))
config = import_module("world").config
C = munchify(config)["servers"]
fastServers = [k for k in C.keys() if "fast" in C[k].keys() and C[k]["group"]!="orchestrators"]
STATES = {S: requests.post(f"http://{C[S].host}:{C[S].port}/{S}/get_status").json() for S in fastServers}

# END TESTING


app = FastAPI(title=servKey,
              description="Async orchestrator with blocking", version=0.1)


@app.on_event("startup")
async def startup_event():
    global orch
    orch = OrchHandler(C)
    asyncio.create_task(orch.monitor_states())
    
    
@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    while True:
        # only broadcast orch status if running; status messages should only generate while running
        if orch.status != 'idle':
            data = await orch.msgq.get()
            await websocket.send_text(json.dumps(data))
            orch.msgq.task_done()

@app.websocket(f"/{servKey}/ws_data")
async def websocket_data(websocket: WebSocket):
    await websocket.accept()
    while True:
        # only broadcast orch status if running; status messages should only generate while running
        if orch.status != 'idle':
            data = await orch.dataq.get()
            await websocket.send_text(json.dumps(data))
            orch.dataq.task_done()
    
    
@app.post(f"/{servKey}/start")
async def start_process():
    if orch.status == 'idle':
        # just in case status messages were populated, clear before starting
        while not orch.msgq.empty():
            _ = await orch.msgq.get()
        if orch.actions or orch.decisions:  # resume actions from a paused run
            await run_dispatch_loop()
        else:
            print('decision list is empty')
    else:
        print('already running')
    return {}

@app.post(f"/{servKey}/stop")
def stop_process():
    if orch.status != 'idle':
        orch.update('stopping')
    else:
        print('orchestrator is not running')
    return {}
    
@app.post(f"/{servKey}/skip")
def skip_decision():
    if orch.status != 'idle':
        orch.update('skipping')
    else:
        print('orchestrator is not running')
    return {}

@app.post(f"{servKey}/clear_queue")
def clear_decisions():
    return {}


# async_dispatcher executes an action, the action tuple 
async def async_dispatcher(action_tup):
    provenance, (server, action, params, preempt, block) = action_tup
    S = C[server]
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{S.host}:{S.port}/{server}/{action}", params=params) as resp:
            response = await resp.text()
    return response


# async def run_dispatch_loop():
#     # if action list is empty but decisions are pending, populate actions
#     if orch.decisions and not orch.actions:
#         decision_id, act_gen = orch.decisions.popleft()
#         orch.procid = decision_id
#         orch.actions = deque(act_gen(decision_id))
#     # resume actions
#     while orch.actions or orch.status!='idle': # clause for resuming paused action list
#         # execute actions sequentially, if blocking action wait for block to clear
#         if orch.status=='stopping':
#             print('stopped')
#             orch.update('idle')
#         elif orch.status=='skipping':
#             if orch.decisions:
#                 decision_id, act_gen = orch.decisions.popleft()
#                 orch.actions = deque(act_gen(decision_id))
#                 orch.procid = decision_id
#                 orch.status.update('running')
#             else:
#                 orch.actions.clear()
#                 orch.update('idle')
#         elif orch.status=='running':
#             current_act = orch.actions.popleft()
#             block, preempt = current_act[4:6] # see async_dispatcher for unpacking
#             if preempt:
#                 while any([orch.STATES[k]['status'] != 'idle' for k in orch.STATES.keys()]):
#                     _ = await orch.dataq.get() # just used to monitor orch.STATES update
#                     orch.dataq.task_done()
#             if block or not orch.actions: # final action, treat as blocking
#                 orch.blocked = True
#                 await async_dispatcher(current_act)
#                 orch.blocked = False
#             else:
#                 asyncio.create_task(async_dispatcher(current_act))
#             # action list now empty, get new decision
#             if orch.decisions and not orch.actions:
#                 decision_id, act_gen = orch.decisions.popleft()
#                 orch.procid = decision_id
#                 orch.actions = deque(act_gen(decision_id))
#             # elif not orch.decisions and not orch.actions:  # generate new decisions
#     orch.update('idle')
#     return True
    
async def run_dispatch_loop():
    while orch.status != 'idle' and (orch.actions or orch.decisions):  # clause for resuming paused action list
        if not orch.actions:
            decision_id, act_gen = orch.decisions.popleft()
            orch.procid = decision_id
            orch.actions = deque(act_gen(decision_id))
        else:
            if orch.status == 'stopping':
                while any([orch.STATES[k]['status'] != 'idle' for k in orch.STATES.keys()]):
                    _ = await orch.dataq.get()  # just used to monitor orch.STATES update
                    orch.dataq.task_done()
                print('stopped')
                orch.update('idle')
            elif orch.status == 'skipping':
                print('skipped')
                orch.actions.clear()
            elif orch.status == 'running':
                current_act = orch.actions.popleft()
                # see async_dispatcher for unpacking
                block, preempt = current_act[4:6]
                if preempt:
                    while any([orch.STATES[k]['status'] != 'idle' for k in orch.STATES.keys()]):
                        _ = await orch.dataq.get()  # just used to monitor orch.STATES update
                        orch.dataq.task_done()
                if block or not orch.actions:  # final action, treat as blocking
                    orch.blocked = True
                    await async_dispatcher(current_act)
                    orch.blocked = False
                else:
                    asyncio.create_task(async_dispatcher(current_act))
                # TODO: dynamic generate new decisions
                # if not orch.decisions and not orch.actions
    orch.update('idle')
    return True


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
    uvicorn.run(app, host=O.host, port=O.port)
