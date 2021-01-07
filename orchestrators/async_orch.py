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
sys.path.append(os.path.join(helao_root, 'core'))
from classes import OrchHandler, Decision, Action

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

# import action generators from action library
sys.path.append(os.path.join(helao_root, 'library'))
for actlib in config['action_libraries']:
    actlibd = import_module(actlib).__dict__
    globals().update({func: actlibd[func] for func in actlibd['actualizers']})
        

# # TESTING
# import os, sys, json, requests, asyncio, websockets
# from importlib import import_module
# from munch import munchify

# sys.path.append(os.path.join(os.getcwd(), 'config'))
# config = import_module("world").config
# C = munchify(config)["servers"]
# fastServers = [k for k in C.keys() if "fast" in C[k].keys() and C[k]["group"]!="orchestrators"]
# STATES = {S: requests.post(f"http://{C[S].host}:{C[S].port}/{S}/get_status").json() for S in fastServers}

# # END TESTING


app = FastAPI(title=servKey,
              description="Async orchestrator with blocking", version=0.1)


@app.on_event("startup")
async def startup_event():
    global orch
    orch = OrchHandler(C)
    asyncio.create_task(orch.monitor_states())
    orch.decisions.append(Decision(uid='0001', plate_id=1234, sample_no=9, actualizer=oer_screen))
    orch.decisions.append(Decision(uid='0002', plate_id=1234, sample_no=12, actualizer=oer_screen))
    orch.decisions.append(Decision(uid='0003', plate_id=1234, sample_no=15, actualizer=oer_screen))
    print(len(orch.decisions))

@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    while True:
        # only broadcast orch status if running; status messages should only generate while running
        if orch.status != 'idle':
            data = await orch.msgq.get()
            await websocket.send_text(json.dumps(data))
            print(json.dumps(data))
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
        orch.raise_stop()
    else:
        print('orchestrator is not running')
    return {}
    
@app.post(f"/{servKey}/skip")
def skip_decision():
    if orch.status != 'idle':
        orch.raise_skip()
    else:
        print('orchestrator not running, clearing action queue')
        orch.actions.clear()
    return {}

@app.post(f"{servKey}/clear_queue")
def clear_decisions():
    print('clearing action queue')
    orch.actions.clear()
    return {}

@app.post(f"{servKey}/reset_demo")
def reset_demo():
    orch.decisions.append(Decision(uid='0001', plate_id=1234, sample_no=9, actualizer=oer_screen))
    orch.decisions.append(Decision(uid='0002', plate_id=1234, sample_no=12, actualizer=oer_screen))
    orch.decisions.append(Decision(uid='0003', plate_id=1234, sample_no=15, actualizer=oer_screen))
    return {}

# async_dispatcher executes an action, the action tuple 
async def async_dispatcher(A: Action):
    S = C[A.server]
    # if A.block or not orch.actions: # if action is blocking, block orchestrator before execution
    #     orch.block()
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{S.host}:{S.port}/{A.server}/{A.action}", params=A.pars) as resp:
            response = await resp.text()
    # if A.block or not orch.actions: # after action is complete, unblock orchestrator
    #     orch.unblock()
    return response


def sync_dispatcher(A: Action):
    S = C[A.server]
    # if A.block or not orch.actions: # if action is blocking, block orchestrator before execution
    #     orch.block()
    with requests.Session() as session:
        with session.post(f"http://{S.host}:{S.port}/{A.server}/{A.action}", params=A.pars) as resp:
            response = resp.text
    # if A.block or not orch.actions: # after action is complete, unblock orchestrator
    #     orch.unblock()
    return response

    
async def run_dispatch_loop():
    if orch.status == 'idle':
        await orch.set_run()
    while orch.status != 'idle' and (orch.actions or orch.decisions):  # clause for resuming paused action list
        if not orch.actions:
            D = orch.decisions.popleft()
            orch.procid = D.uid
            orch.actions = deque(D.actualizer(D))
        else:
            if orch.status == 'stopping':
                print('stop issued: waiting for action servers to idle')
                while any([orch.STATES[k]['status'] != 'idle' for k in orch.STATES.keys()]):
                    _ = await orch.dataq.get()  # just used to monitor orch.STATES update
                    orch.dataq.task_done()
                print('stopped')
                orch.set_idle()
            elif orch.status == 'skipping':
                print('skipping to next decision')
                orch.actions.clear()
                orch.set_run()
            elif orch.status == 'running':
                # check current blocking status
                while orch.is_blocked:
                    print('waiting for orchestrator to unblock')
                    _ = await orch.dataq.get()
                    orch.dataq.task_done()
                A = orch.actions.popleft()
                # see async_dispatcher for unpacking
                if A.preempt:
                    while any([orch.STATES[k]['status'] != 'idle' for k in orch.STATES.keys()]):
                        print(orch.STATES)
                        _ = await orch.dataq.get()
                        orch.dataq.task_done()
                print(f"dispatching action {A.action} on server {A.server}")
                if A.block or not orch.actions: # block if flag is set, or last action in queue
                    orch.block()
                    print(f'[{A.decision.uid} / {A.action}] blocking - sync action started')
                    sync_dispatcher(A)
                    orch.unblock()
                    print(f'[{A.decision.uid} / {A.action}] unblocked - sync action finished')
                else:
                    print(f'[{A.decision.uid} / {A.action}] no blocking - async action started')
                    asyncio.create_task(async_dispatcher(A))
                    print(f'[{A.decision} / {A.action}] no blocking - async action finished')
                # TODO: dynamic generate new decisions by signaling operator
                # if not orch.decisions and not orch.actions
    print('decision queue is empty')
    await orch.set_idle()
    return True

@app.post('/append_decision')
def append_decision():
    return ''
@app.post('/prepend_decision')
def prepend_decision():
    return ''
@app.post('/list_decisions')
def list_decisions():
    return ''


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
