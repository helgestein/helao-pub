# shell: uvicorn motion_server:app --reload
""" A FastAPI service definition for a potentiostat device server, e.g. Gamry.

The potentiostat service defines RESTful methods for sending commmands and retrieving 
data from a potentiostat driver class such as 'gamry_driver' or 'gamry_simulate' using
FastAPI. The methods provided by this service are not device-specific. Appropriate code
must be written in the driver class to ensure that the service methods are generic, i.e.
calls to 'poti.*' are not device-specific. Currently inherits configuration from driver 
code, and hard-coded to use 'gamry' class (see "__main__").

IMPORTANT -- class methods which are "blocking" i.e. synchronous driver calls must be
preceded by:
  await stat.set_run()
and followed by :
  await stat.set_idle()
which will update this action server's status dictionary which is query-able via
../get_status, and also broadcast the status change via websocket ../ws_status

IMPORTANT -- this framework assumes a single data stream and structure produced by the
low level device driver, so ../ws_data will only broadcast the device class's  poti.q;
additional data streams may be added as separate websockets or reworked into present
../ws_data columar format with an additional tag column to differentiate streams



Manual Bugfixes:
    https://github.com/chrullrich/comtypes/commit/6d3934b37a5d614a6be050cbc8f09d59bceefcca

"""

import os
import sys
from importlib import import_module
import asyncio


import uvicorn
from fastapi import WebSocket
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from typing import Optional
from prototyping import Action, HelaoFastAPI, Base

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


# check if 'simulate' settings is present
if not 'simulate' in S:
    # default if no simulate is defined
    print('"simulate" not defined, switching to Gamry Simulator.')
    S['simulate']= False


if S.simulate:
    print('Gamry simulator loaded.')
    from gamry_simulate import gamry
else:
    from gamry_driver import gamry
    from gamry_driver import Gamry_Irange


app = HelaoFastAPI(config, servKey, title=servKey,
              description="Gamry instrument/action server", version=2.0)


@app.on_event("startup")
def startup_event():
    global actserv
    actserv = Base(app)
    global poti
    poti = gamry(actserv)


@app.websocket("/ws_status")
async def websocket_status(websocket: WebSocket):
    """Broadcast status messages.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await actserv.ws_status(websocket)


@app.websocket("/ws_data")
async def websocket_data(websocket: WebSocket):
    """Broadcast status dicts.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await actserv.ws_data(websocket)
    

@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return actserv.status


@app.post(f"/{servKey}/get_meas_status")
async def get_meas_status(action_dict: Optional[dict]=None):
    """Will return 'idle' or 'measuring'. Should be used in conjuction with eta to async.sleep loop poll"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "get_meas_status"
    active = await actserv.contain_action(A)
    await active.enqueue_data({"status": await poti.status()})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/run_LSV")
async def run_LSV(
    Vinit: Optional[float] = 0.0,         # Initial value in volts or amps.
    Vfinal: Optional[float] = 1.0,        # Final value in volts or amps.
    ScanRate: Optional[float] = 1.0,      # Scan rate in volts/second or amps/second.
    SampleRate: Optional[float] = 0.01,   # Time between data acquisition samples in seconds.
    TTLwait: Optional[int] = -1,          # -1 disables, else select TTL 0-3
    TTLsend: Optional[int] = -1,           # -1 disables, else select TTL 0-3
    IErange: Optional[Gamry_Irange] = 'auto',
    action_dict: Optional[dict] = None, #optional parameters
):
    """Linear Sweep Voltammetry (unlike CV no backward scan is done)\n
    use 4bit bitmask for triggers\n
    IErange depends on gamry model used (test actual limit before using)"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "run_LSV"
        A.action_params['Vinit'] = Vinit
        A.action_params['Vfinal'] = Vfinal
        A.action_params['ScanRate'] = ScanRate
        A.action_params['SampleRate'] = SampleRate
        A.action_params['TTLwait'] = TTLwait
        A.action_params['TTLsend'] = TTLsend
        A.action_params['IErange'] = IErange
    active_dict = poti.technique_LSV(A)
    return active_dict


@app.post(f"/{servKey}/run_CA")
async def run_CA(
    Vval: Optional[float] = 0.0,
    Tval: Optional[float] = 10.0,
    SampleRate: Optional[float] = 0.01,    # Time between data acquisition samples in seconds.
    TTLwait: Optional[int] = -1, # -1 disables, else select TTL 0-3
    TTLsend: Optional[int] = -1, # -1 disables, else select TTL 0-3
    IErange: Optional[Gamry_Irange] = 'auto',
    action_dict: Optional[dict]=None, #optional parameters
):
    """Chronoamperometry (current response on amplied potential)\n
    use 4bit bitmask for triggers\n
    IErange depends on gamry model used (test actual limit before using)"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "run_CA"
        A.action_params['Vval'] = Vval
        A.action_params['Tval'] = Tval
        A.action_params['SampleRate'] = SampleRate
        A.action_params['TTLwait'] = TTLwait
        A.action_params['TTLsend'] = TTLsend
        A.action_params['IErange'] = IErange
    active_dict = poti.technique_CA(A)
    return active_dict


@app.post(f"/{servKey}/run_CP")
async def run_CP(
    Ival: Optional[float] = 0.0,
    Tval: Optional[float] = 10.0,
    SampleRate: Optional[float] = 1.0,      # Time between data acquisition samples in seconds.
    TTLwait: Optional[int] = -1, # -1 disables, else select TTL 0-3
    TTLsend: Optional[int] = -1, # -1 disables, else select TTL 0-3
    IErange: Optional[Gamry_Irange] = 'auto',
    action_dict: Optional[dict]=None, #optional parameters
):
    """Chronopotentiometry (Potential response on controlled current)\n
    use 4bit bitmask for triggers\n
    IErange depends on gamry model used (test actual limit before using)"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "run_CP"
        A.action_params['Ival'] = Ival
        A.action_params['Tval'] = Tval
        A.action_params['SampleRate'] = SampleRate
        A.action_params['TTLwait'] = TTLwait
        A.action_params['TTLsend'] = TTLsend
        A.action_params['IErange'] = IErange
    active_dict = poti.technique_CP(A)
    return active_dict


@app.post(f"/{servKey}/run_CV")
async def run_CV(
    Vinit: Optional['float'] = 0.0,           # Initial value in volts or amps.
    Vapex1: Optional['float'] = 1.0,          # Apex 1 value in volts or amps.
    Vapex2: Optional['float'] = -1.0,         # Apex 2 value in volts or amps.
    Vfinal: Optional['float'] = 0.0,          # Final value in volts or amps.
    ScanRate: Optional['float'] = 1.0,        # Apex scan rate in volts/second or amps/second.
    SampleRate: Optional['float'] = 0.01,     # Time between data acquisition steps.
    Cycles: Optional['int'] = 1,
    TTLwait: Optional['int'] = -1, # -1 disables, else select TTL 0-3
    TTLsend: Optional['int'] = -1, # -1 disables, else select TTL 0-3
    IErange: Optional['Gamry_Irange'] = 'auto',
    action_dict: Optional[dict]=None, #optional parameters
):
    """Cyclic Voltammetry (most widely used technique for acquireing information about electrochemical reactions)\n
    use 4bit bitmask for triggers\n
    IErange depends on gamry model used (test actual limit before using)"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "run_CV"
        A.action_params['Vinit'] = Vinit
        A.action_params['Vapex1'] = Vapex1
        A.action_params['Vapex2'] = Vapex2
        A.action_params['Vfinal'] = Vfinal
        A.action_params['ScanRate'] = ScanRate
        A.action_params['SampleRate'] = SampleRate
        A.action_params['Cycles'] = Cycles
        A.action_params['TTLwait'] = TTLwait
        A.action_params['TTLsend'] = TTLsend
        A.action_params['IErange'] = IErange
    active_dict = poti.technique_CV(A)
    return active_dict


@app.post(f"/{servKey}/run_EIS")
async def run_EIS(
    Vval: Optional[float] = 0.0,
    Tval: Optional[float] = 10.0,
    Freq: Optional[float] = 1000.0,
    RMS: Optional[float] = 0.02, 
    Precision: Optional[float] = 0.001, #The precision is used in a Correlation Coefficient (residual power) based test to determine whether or not to measure another cycle.
    SampleRate: Optional[float] = 0.01,
    TTLwait: Optional[int] = -1, # -1 disables, else select TTL 0-3
    TTLsend: Optional[int] = -1, # -1 disables, else select TTL 0-3
    IErange: Optional[Gamry_Irange] = 'auto',
    action_dict: Optional[dict]=None, #optional parameters
):
    """Electrochemical Impendance Spectroscopy\n
    NOT TESTED\n
    use 4bit bitmask for triggers\n
    IErange depends on gamry model used (test actual limit before using)"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "run_CV"
        A.action_params['Vval'] = Vval
        A.action_params['Tval'] = Tval
        A.action_params['Freq'] = Freq
        A.action_params['RMS'] = RMS
        A.action_params['Precision'] = Precision
        A.action_params['SampleRate'] = SampleRate
        A.action_params['TTLwait'] = TTLwait
        A.action_params['TTLsend'] = TTLsend
        A.action_params['IErange'] = IErange
    active_dict = poti.technique_EIS(A)
    return active_dict


@app.post(f"/{servKey}/run_OCV")
async def run_OCV(
    Tval: Optional[float] = 10.0,
    SampleRate: Optional[float] = 0.01,
    TTLwait: Optional[int] = -1, # -1 disables, else select TTL 0-3
    TTLsend: Optional[int] = -1, # -1 disables, else select TTL 0-3
    IErange: Optional[Gamry_Irange] = 'auto',
    action_dict: Optional[dict]=None, #optional parameters
):
    """mesasures open circuit potential\n
    use 4bit bitmask for triggers\n
    IErange depends on gamry model used (test actual limit before using)"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "run_OCV"
        A.action_params['Tval'] = Tval
        A.action_params['SampleRate'] = SampleRate
        A.action_params['TTLwait'] = TTLwait
        A.action_params['TTLsend'] = TTLsend
        A.action_params['IErange'] = IErange
    active_dict = poti.technique_OCV(A)
    return active_dict


@app.post(f"/{servKey}/stop")
async def stop(action_dict: Optional[dict]=None):
    """Stops measurement in a controlled way."""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "stop"
    active = await actserv.cotnain_action(A)
    await active.enqueue_data({"stop_result": await poti.stop()})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post(f"/{servKey}/estop")
async def estop(switch: Optional[bool] = True, action_dict: Optional[dict]=None):
    """Same as stop, but also sets estop flag."""
    if action_dict:
        A = Action(action_dict)
        switch = A.action_params["switch"]
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "estop"
        A.action_params["switch"] = switch
    active = await actserv.cotnain_action(A)
    await active.enqueue_data({"estop_result": await poti.estop(switch)})
    finished_act = await active.finish()
    return finished_act.as_dict()


@app.post('/endpoints')
def get_all_urls():
    """Return a list of all endpoints on this server."""
    return actserv.get_endpoint_urls(app)


@app.post("/shutdown")
def post_shutdown():
    #asyncio.gather(poti.close_connection())
    poti.kill_GamryCom()
#    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
    # this gets called when the server is shut down or reloaded to ensure a clean
    # disconnect ... just restart or terminate the server
    asyncio.gather(poti.close_connection())
    poti.kill_GamryCom()
    return {"shutdown"}


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
