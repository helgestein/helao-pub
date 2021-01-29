# -*- coding: utf-8 -*-
"""Asynchronous orchestrator example.

This server implements a general-purpose orchestrator capable of executing a mixed queue
of synchronous and asynchronous actions. It provides POST request endpoints for managing
a OrchHandler class object, the core functionality of an async orchestrator.

    Startup:
    The orchestrator server must be started AFTER all instrument and action servers
    within a configuration file. Creating server processes via the helao.py launch
    script enforces the required launch order.

    After instantiating the global OrchHandler, the object will subscribe to all action
    server status websockets using the .monitor_states() coroutine. Websocket messages
    coming from action servers will update the OrchHandler's asyncio 'data' queue, which
    in turn acts as a trigger for checks to the global blocking status while running the
    orchestrator's action dispatch loop. This design avoids continuous polling on the
    global blocking status.

    Queue:
    The orchestrator uses deque objects to maintain separate sample and action queues.
    The sample queue may be populated using POST requests to '/append_decision' or
    '/prepend_decision' endpoints. The action queue is determined by the 'actualizer'
    method of a given sample [decision]. Actualizers are defined in an action library
    specified by the configuration. An actualizer takes a sample argument and returns a
    list of actions. The action queue is repopulated once all actions on a given sample
    have finished (this prevents simultaneous execution of actions across samples).

    Dispatch:
    Sample and action queues are processed by the 'run_dispatch_loop' coroutine, which
    is created by posting a request to the '/start' server endpoint. The corresponding
    '/stop' endpoint is used to end processing but at the moment does not interrupt any
    actions in progress.

    TODO:
    Consider moving all logic into OrchHandler class, so other orchestrators only need
    to define FastAPI server endpoints.
"""

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

# Not packaging as a module for now, so we detect source file's root directory from CLI
# execution and append config, driver, and core to sys.path
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, "config"))
sys.path.append(os.path.join(helao_root, "driver"))
sys.path.append(os.path.join(helao_root, "core"))
from classes import OrchHandler, Decision, Action

# Load configuration using CLI launch parameters. For shorthand referencing the config
# dictionary, we use munchify to convert into a dict-compatible object where dict keys
# are also attributes.
confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
O = C[servKey]

# Multiple action libraries may be specified in the config, and all actualizers will be
# imported into the action_lib dictionary. When importing more than one action library,
# take care that actualizer function names do not conflict.
action_lib = {}
sys.path.append(os.path.join(helao_root, "library"))
for actlib in config["action_libraries"]:
    tempd = import_module(actlib).__dict__
    action_lib.update({func: tempd[func] for func in tempd["ACTUALIZERS"]})

app = FastAPI(
    title=servKey, description="Async orchestrator with blocking", version=0.1
)


@app.on_event("startup")
def startup_event():
    """Run startup actions.

    When FastAPI server starts, create a global OrchHandler object, initiate the
    monitor_states coroutine which runs forever, and append dummy decisions to the
    decision queue for testing.
    """
    global orch
    orch = OrchHandler(C)
    # TODO: write class method to launch monitor_states coro in current event loop
    # global monitor_task
    # monitor_task = asyncio.create_task(orch.monitor_states())
    orch.monitor_states()
    # populate decisions for testing
    orch.decisions.append(
        Decision(
            uid="0001", plate_id=1234, sample_no=9, actualizer=action_lib["oer_screen"]
        )
    )
    orch.decisions.append(
        Decision(
            uid="0002", plate_id=1234, sample_no=12, actualizer=action_lib["oer_screen"]
        )
    )
    orch.decisions.append(
        Decision(
            uid="0003", plate_id=1234, sample_no=15, actualizer=action_lib["oer_screen"]
        )
    )
    print(len(orch.decisions))


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    """Subscribe to orchestrator status messages.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await websocket.accept()
    while True:
        # only broadcast orch status if running; status messages should only generate while running
        if orch.status != "idle":
            data = await orch.msgq.get()
            await websocket.send_text(json.dumps(data))
            print(json.dumps(data))
            orch.msgq.task_done()


@app.websocket(f"/{servKey}/ws_data")
async def websocket_data(websocket: WebSocket):
    """Subscribe to action server status dicts.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await websocket.accept()
    while True:
        # only broadcast orch status if running; status messages should only generate while running
        if orch.status != "idle":
            data = await orch.dataq.get()
            await websocket.send_text(json.dumps(data))
            orch.dataq.task_done()


@app.post(f"/{servKey}/start")
async def start_process():
    """Begin processing decision and action queues."""
    if orch.status == "idle":
        # just in case status messages were populated, clear before starting
        while not orch.msgq.empty():
            _ = await orch.msgq.get()
        if orch.actions or orch.decisions:  # resume actions from a paused run
            await run_dispatch_loop()
            # asyncio.create_task(run_dispatch_loop())
        else:
            print("decision list is empty")
    else:
        print("already running")
    return {}


@app.post(f"/{servKey}/stop")
async def stop_process():
    """Stop processing decision and action queues."""
    if orch.status != "idle":
        await orch.raise_stop()
    else:
        print("orchestrator is not running")
    return {}


@app.post(f"/{servKey}/skip")
async def skip_decision():
    """Clear the present action queue while running."""
    if orch.status != "idle":
        await orch.raise_skip()
    else:
        print("orchestrator not running, clearing action queue")
        orch.actions.clear()
    return {}


@app.post(f"/{servKey}/clear_actions")
def clear_actions():
    """Clear the present action queue while stopped."""
    print("clearing action queue")
    orch.actions.clear()
    return {}


@app.post(f"/{servKey}/clear_decisions")
def clear_decisions():
    """Clear the present decision queue while stopped."""
    print("clearing decision queue")
    orch.decisions.clear()
    return {}


@app.post(f"/{servKey}/reset_demo")
def reset_demo():
    """Re-add example decisions to decision queue."""
    orch.decisions.append(
        Decision(
            uid="0001", plate_id=1234, sample_no=9, actualizer=action_lib["oer_screen"]
        )
    )
    orch.decisions.append(
        Decision(
            uid="0002", plate_id=1234, sample_no=12, actualizer=action_lib["oer_screen"]
        )
    )
    orch.decisions.append(
        Decision(
            uid="0003", plate_id=1234, sample_no=15, actualizer=action_lib["oer_screen"]
        )
    )
    return {}


# TODO: move async_dispatcher, sync_dispatcher,  and run_dispatch_loop into OrchHandler
async def async_dispatcher(A: Action):
    """Request non-blocking actions which may run concurrently.

    Args:
      A: an Action type object containing action server name, endpoint, and parameters.

    Returns:
      Response string from http POST request.
    """
    S = C[A.server]
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://{S.host}:{S.port}/{A.server}/{A.action}", params=A.pars
        ) as resp:
            response = await resp.text()
    return response


def sync_dispatcher(A: Action):
    """Request blocking actions which must run sequentially.

    Args:
      A: an Action type object containing action server name, endpoint, and parameters.

    Returns:
      Response string from http POST request.
    """
    S = C[A.server]
    with requests.Session() as session:
        with session.post(
            f"http://{S.host}:{S.port}/{A.server}/{A.action}", params=A.pars
        ) as resp:
            response = resp.text
    return response


async def run_dispatch_loop():
    """Parse decision and action queues, and dispatch actions."""
    if orch.status == "idle":
        await orch.set_run()
    # clause for resuming paused action list
    while orch.status != "idle" and (orch.actions or orch.decisions):
        await asyncio.sleep(
            0.01
        )  # await point allows status changes to affect between actions
        if not orch.actions:
            D = orch.decisions.popleft()
            orch.procid = D.uid
            orch.actions = deque(D.actualizer(D))
        else:
            if orch.status == "stopping":
                print("stop issued: waiting for action servers to idle")
                while any(
                    [orch.STATES[k]["status"] != "idle" for k in orch.STATES.keys()]
                ):
                    _ = (
                        await orch.dataq.get()
                    )  # just used to monitor orch.STATES update
                    orch.dataq.task_done()
                print("stopped")
                orch.set_idle()
            elif orch.status == "skipping":
                print("skipping to next decision")
                orch.actions.clear()
                orch.set_run()
            elif orch.status == "running":
                # check current blocking status
                while orch.is_blocked:
                    print("waiting for orchestrator to unblock")
                    _ = await orch.dataq.get()
                    orch.dataq.task_done()
                A = orch.actions.popleft()
                # see async_dispatcher for unpacking
                if A.preempt:
                    while any(
                        [orch.STATES[k]["status"] != "idle" for k in orch.STATES.keys()]
                    ):
                        print(orch.STATES)
                        _ = await orch.dataq.get()
                        orch.dataq.task_done()
                print(f"dispatching action {A.action} on server {A.server}")
                if (
                    A.block or not orch.actions
                ):  # block if flag is set, or last action in queue
                    orch.block()
                    print(
                        f"[{A.decision.uid} / {A.action}] blocking - sync action started"
                    )
                    sync_dispatcher(A)
                    orch.unblock()
                    print(
                        f"[{A.decision.uid} / {A.action}] unblocked - sync action finished"
                    )
                else:
                    print(
                        f"[{A.decision.uid} / {A.action}] no blocking - async action started"
                    )
                    await async_dispatcher(A)
                    print(
                        f"[{A.decision.uid} / {A.action}] no blocking - async action finished"
                    )
                # TODO: dynamic generate new decisions by signaling operator
                # if not orch.decisions and not orch.actions
    print("decision queue is empty")
    await orch.set_idle()
    return True


@app.post(f"/{servKey}/append_decision")
def append_decision(uid: str, plate_id: int, sample_no: int, actualizer: str):
    """Add a decision object to the end of the decision queue.

    Args:
      uid: A unique decision identifier, as str.
      plate_id: The sample's plate id (no checksum), as int.
      sample_no: A sample number, as int.
      actualizer: The name of the actualizer for building the action list, as str.

    Returns:
      Nothing.
    """
    orch.decisions.append(
        (
            Decision(
                uid=uid,
                plate_id=plate_id,
                sample_no=sample_no,
                actualizer=action_lib[actualizer],
            )
        )
    )
    return {}


@app.post(f"/{servKey}/prepend_decision")
def prepend_decision(uid: str, plate_id: int, sample_no: int, actualizer: str):
    """Add a decision object to the start of the decision queue.

    Args:
      uid: A unique decision identifier, as str.
      plate_id: The sample's plate id (no checksum), as int.
      sample_no: A sample number, as int.
      actualizer: The name of the actualizer for building the action list, as str.

    Returns:
      Nothing.
    """
    orch.decisions.appendleft(
        (
            Decision(
                uid=uid,
                plate_id=plate_id,
                sample_no=sample_no,
                actualizer=action_lib[actualizer],
            )
        )
    )
    return {}


class return_dec(BaseModel):
    """Return class for queried Decision objects."""

    index: int
    uid: str
    plate_id: int
    sample_no: int
    actualizer: str
    timestamp: str


class return_declist(BaseModel):
    """Return class for queried Decision list."""

    decisions: List[return_dec]


class return_act(BaseModel):
    """Return class for queried Action objects."""

    index: int
    uid: str
    server: str
    action: str
    pars: dict
    preempt: bool
    block: bool
    timestamp: str


class return_actlist(BaseModel):
    """Return class for queried Action list."""

    actions: List[return_act]


@app.post(f"/{servKey}/list_decisions")
def list_decisions():
    """Return the current list of decisions."""
    declist = [
        return_dec(
            index=i,
            uid=dec.uid,
            plate_id=dec.plate_id,
            sample_no=dec.sample_no,
            actualizer=dec.actualizer.__name__,
            timestamp=dec.created_at,
        )
        for i, dec in enumerate(orch.decisions)
    ]
    retval = return_declist(decisions=declist)
    return retval


@app.post(f"/{servKey}/list_actions")
def list_actions():
    """Return the current list of actions."""
    actlist = [
        return_act(
            index=i,
            uid=act.decision.uid,
            server=act.server,
            action=act.action,
            pars=act.pars,
            preempt=act.preempt,
            block=act.block,
            timestamp=act.created_at,
        )
        for i, act in enumerate(orch.actions)
    ]
    retval = return_actlist(actions=actlist)
    return retval


@app.post(f"/shutdown")
def pre_shutdown_tasks():
    """Execute code before terminating with helao.py script."""
    for k, task in orch.monitors.items():
        task.cancel()
        print(f'Cancelled {k} websocket monitor')


@app.post("/endpoints")
def get_all_urls():
    """Return a list of all endpoints on this server."""
    url_list = []
    for route in app.routes:
        routeD = {"path": route.path, "name": route.name}
        if "dependant" in dir(route):
            flatParams = get_flat_params(route.dependant)
            paramD = {
                par.name: {
                    "outer_type": str(par.outer_type_).split("'")[1],
                    "type": str(par.type_).split("'")[1],
                    "required": par.required,
                    "shape": par.shape,
                    "default": par.default,
                }
                for par in flatParams
            }
            routeD["params"] = paramD
        else:
            routeD["params"] = []
        url_list.append(routeD)
    return url_list


@app.on_event("shutdown")
def disconnect():
    """Run shutdown actions."""
    emergencyStop = True
    time.sleep(0.75)


if __name__ == "__main__":
    uvicorn.run(app, host=O.host, port=O.port)
