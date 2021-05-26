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
import time
import asyncio
from importlib import import_module

import uvicorn
from fastapi import WebSocket
from munch import munchify

# Not packaging as a module for now, so we detect source file's root directory from CLI
# execution and append config, driver, and core to sys.path
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, "config"))
sys.path.append(os.path.join(helao_root, "driver"))
sys.path.append(os.path.join(helao_root, "core"))
from prototyping import Action, Decision, Orch, HelaoFastAPI

# Load configuration using CLI launch parameters. For shorthand referencing the config
# dictionary, we use munchify to convert into a dict-compatible object where dict keys
# are also attributes.
confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
O = C[servKey]
app = HelaoFastAPI(
    config, servKey, title=servKey, description="Async orchestrator V2", version=0.2
)


@app.on_event("startup")
async def startup_event():
    """Run startup actions.

    When FastAPI server starts, create a global OrchHandler object, initiate the
    monitor_states coroutine which runs forever, and append dummy decisions to the
    decision queue for testing.
    """
    global orch
    orch = Orch(servKey, app)


@app.websocket(f"/ws_status")
async def websocket_status(websocket: WebSocket):
    """Subscribe to orchestrator status messages.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await orch.ws_status(websocket)


@app.websocket(f"/ws_data")
async def websocket_data(websocket: WebSocket):
    """Subscribe to action server status dicts.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await orch.ws_data(websocket)


@app.post(f"/start")
async def start_process():
    """Begin processing decision and action queues."""
    if orch.loop_state == "stopped":
        if orch.actions or orch.decisions:  # resume actions from a paused run
            await orch.run_dispatch_loop()
        else:
            print("decision list is empty")
    else:
        print("already running")
    return {}


@app.post(f"/stop")
async def stop_process():
    """Stop processing decision and action queues."""
    if orch.loop_state == "started":
        await orch.intend_stop()
    else:
        print("orchestrator is not running")
    return {}


@app.post(f"/skip")
async def skip_decision():
    """Clear the present action queue while running."""
    if orch.loop_state == "started":
        await orch.intend_skip()
    else:
        print("orchestrator not running, clearing action queue")
        await asyncio.sleep(0.001)
        orch.actions.clear()
    return {}


@app.post(f"/{servKey}/clear_actions")
async def clear_actions():
    """Clear the present action queue while stopped."""
    print("clearing action queue")
    await asyncio.sleep(0.001)
    orch.actions.clear()
    return {}


@app.post(f"/{servKey}/clear_decisions")
async def clear_decisions():
    """Clear the present decision queue while stopped."""
    print("clearing decision queue")
    await asyncio.sleep(0.001)
    orch.decisions.clear()
    return {}


@app.post(f"/{servKey}/append_decision")
async def append_decision(
    decision_dict: dict = None,
    orch_name: str = None,
    decision_label: str = None,
    plate_id: int = None,
    sample_no: int = None,
    samples_in: list = [],
    samples_out: list = [],
    actualizer: str = None,
    actual_pars: dict = {},
    result_dict: dict = {},
    access: str = "hte",
):
    """Add a decision object to the end of the decision queue.

    Args:
      decision_dict: Decision parameters (optional), as dict.
      orch_name: Orchestrator server key (optional), as str.
      plate_id: The sample's plate id (no checksum), as int.
      sample_no: A sample number, as int.
      actualizer: The name of the actualizer for building the action list, as str.
      actual_pars: Actualizer parameters, as dict.
      result_dict: Action responses dict keyed by action_enum.
      access: Access control group, as str.

    Returns:
      Nothing.
    """
    await orch.add_decision(
        decision_dict,
        orch_name,
        decision_label,
        plate_id,
        sample_no,
        samples_in,
        samples_out,
        actualizer,
        actual_pars,
        result_dict,
        access,
        prepend=False,
    )
    return {}


@app.post(f"/{servKey}/prepend_decision")
async def prepend_decision(
    decision_dict: dict = None,
    orch_name: str = None,
    decision_label: str = None,
    plate_id: int = None,
    sample_no: int = None,
    samples_in: list = [],
    samples_out: list = [],
    actualizer: str = None,
    actual_pars: dict = {},
    result_dict: dict = {},
    access: str = "hte",
):
    """Add a decision object to the start of the decision queue.

    Args:
      decision_dict: Decision parameters (optional), as dict.
      orch_name: Orchestrator server key (optional), as str.
      plate_id: The sample's plate id (no checksum), as int.
      sample_no: A sample number, as int.
      actualizer: The name of the actualizer for building the action list, as str.
      actual_pars: Actualizer parameters, as dict.
      result_dict: Action responses dict keyed by action_enum.
      access: Access control group, as str.

    Returns:
      Nothing.
    """
    await orch.add_decision(
        decision_dict,
        orch_name,
        decision_label,
        plate_id,
        sample_no,
        samples_in,
        samples_out,
        actualizer,
        actual_pars,
        result_dict,
        access,
        prepend=True,
    )
    return {}


@app.post(f"/list_decisions")
def list_decisions():
    """Return the current list of decisions."""
    return orch.list_decisions()

@app.post(f"/active_decision")
def active_decision():
    """Return the active decision."""
    return orch.get_decision(last=False)

@app.post(f"/last_decision")
def last_decision():
    """Return the last decision."""
    return orch.get_decision(last=True)

@app.post(f"/list_actions")
def list_actions():
    """Return the current list of actions."""
    return orch.list_actions()


@app.post("/endpoints")
def get_all_urls():
    """Return a list of all endpoints on this server."""
    return orch.get_endpoint_urls(app)


@app.on_event("shutdown")
def disconnect():
    """Run shutdown actions."""
    emergencyStop = True
    time.sleep(0.75)


if __name__ == "__main__":
    uvicorn.run(app, host=O.host, port=O.port)
