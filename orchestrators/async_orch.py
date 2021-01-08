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
from pydantic import BaseModel
from typing import List
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
action_lib = {}
sys.path.append(os.path.join(helao_root, 'library'))
for actlib in config['action_libraries']:
    tempd = import_module(actlib).__dict__
    action_lib.update({func: tempd[func] for func in tempd['ACTUALIZERS']})


app = FastAPI(title=servKey,
              description="Async orchestrator with blocking", version=0.1)


@app.on_event("startup")
def startup_event():
    global orch
    orch = OrchHandler(C)
    asyncio.create_task(orch.monitor_states())
    # populate decisions for testing
    orch.decisions.append(Decision(
        uid='0001', plate_id=1234, sample_no=9, actualizer=action_lib['oer_screen']))
    orch.decisions.append(Decision(
        uid='0002', plate_id=1234, sample_no=12, actualizer=action_lib['oer_screen']))
    orch.decisions.append(Decision(
        uid='0003', plate_id=1234, sample_no=15, actualizer=action_lib['oer_screen']))
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
            # asyncio.create_task(run_dispatch_loop())
        else:
            print('decision list is empty')
    else:
        print('already running')
    return {}


@app.post(f"/{servKey}/stop")
async def stop_process():
    if orch.status != 'idle':
        await orch.raise_stop()
    else:
        print('orchestrator is not running')
    return {}


@app.post(f"/{servKey}/skip")
async def skip_decision():
    if orch.status != 'idle':
        await orch.raise_skip()
    else:
        print('orchestrator not running, clearing action queue')
        orch.actions.clear()
    return {}


@app.post(f"/{servKey}/clear_actions")
def clear_actions():
    print('clearing action queue')
    orch.actions.clear()
    return {}

@app.post(f"/{servKey}/clear_decisions")
def clear_decisions():
    print('clearing decision queue')
    orch.decisions.clear()
    return {}

@app.post(f"/{servKey}/reset_demo")
def reset_demo():
    orch.decisions.append(Decision(
        uid='0001', plate_id=1234, sample_no=9, actualizer=action_lib['oer_screen']))
    orch.decisions.append(Decision(
        uid='0002', plate_id=1234, sample_no=12, actualizer=action_lib['oer_screen']))
    orch.decisions.append(Decision(
        uid='0003', plate_id=1234, sample_no=15, actualizer=action_lib['oer_screen']))
    return {}


async def async_dispatcher(A: Action):
    S = C[A.server]
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://{S.host}:{S.port}/{A.server}/{A.action}", params=A.pars) as resp:
            response = await resp.text()
    return response


def sync_dispatcher(A: Action):
    S = C[A.server]
    with requests.Session() as session:
        with session.post(f"http://{S.host}:{S.port}/{A.server}/{A.action}", params=A.pars) as resp:
            response = resp.text
    return response


async def run_dispatch_loop():
    if orch.status == 'idle':
        await orch.set_run()
    # clause for resuming paused action list
    while orch.status != 'idle' and (orch.actions or orch.decisions):
        await asyncio.sleep(0.01) # await point allows status changes to affect between actions
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
                if A.block or not orch.actions:  # block if flag is set, or last action in queue
                    orch.block()
                    print(
                        f'[{A.decision.uid} / {A.action}] blocking - sync action started')
                    sync_dispatcher(A)
                    orch.unblock()
                    print(
                        f'[{A.decision.uid} / {A.action}] unblocked - sync action finished')
                else:
                    print(
                        f'[{A.decision.uid} / {A.action}] no blocking - async action started')
                    await async_dispatcher(A)
                    print(
                        f'[{A.decision.uid} / {A.action}] no blocking - async action finished')
                # TODO: dynamic generate new decisions by signaling operator
                # if not orch.decisions and not orch.actions
    print('decision queue is empty')
    await orch.set_idle()
    return True


@app.post(f'/{servKey}/append_decision')
def append_decision(
    uid: str,
    plate_id: int,
    sample_no: int,
    actualizer: str
):
    orch.decisions.append((Decision(uid=uid, plate_id=plate_id,
                                    sample_no=sample_no, actualizer=action_lib[actualizer])))
    return {}


@app.post(f'/{servKey}/prepend_decision')
def prepend_decision(
    uid: str,
    plate_id: int,
    sample_no: int,
    actualizer: str
):
    orch.decisions.appendleft((Decision(
        uid=uid, plate_id=plate_id, sample_no=sample_no, actualizer=action_lib[actualizer])))
    return {}


class return_dec(BaseModel):
    index: int
    uid: str
    plate_id: int
    sample_no: int
    actualizer: str
    timestamp: str


class return_declist(BaseModel):
    decisions: List[return_dec]


class return_act(BaseModel):
    index: int
    uid: str
    server: str
    action: str
    pars: dict
    preempt: bool
    block: bool
    timestamp: str


class return_actlist(BaseModel):
    actions: List[return_act]


@app.post(f'/{servKey}/list_decisions')
def list_decisions():
    declist = [return_dec(index=i, uid=dec.uid, plate_id=dec.plate_id, sample_no=dec.sample_no,
                          actualizer=dec.actualizer.__name__, timestamp=dec.created_at) for i, dec in enumerate(orch.decisions)]
    retval = return_declist(decisions=declist)
    return retval


@app.post(f'/{servKey}/list_actions')
def list_actions():
    actlist = [return_act(index=i, uid=act.decision.uid, server=act.server, action=act.action, pars=act.pars,
                          preempt=act.preempt, block=act.block, timestamp=act.created_at) for i, act in enumerate(orch.actions)]
    retval = return_actlist(actions=actlist)
    return retval

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
