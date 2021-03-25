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
import json
from importlib import import_module
#from asyncio import Queue
#from time import strftime
import asyncio


import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsHandler
from classes import sample_class

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


app = FastAPI(title=servKey,
              description="Gamry instrument/action server", version=1.0)


@app.on_event("startup")
def startup_event():
    global stat
    stat = StatusHandler()
    global poti
    poti = gamry(S.params, stat)
    global wsdata
    wsdata = wsHandler(poti.wsdataq, 'Gamry wsdata')
    global wsstatus
    wsstatus = wsHandler(stat.q, 'Gamry wsstatus')


@app.websocket(f"/{servKey}/ws_data")
async def websocket_data(websocket: WebSocket):
    await wsdata.websocket_slave(websocket)


# as the technique calls will only start the measurment but won't return the final results
@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.websocket_slave(websocket)
  
        
@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return return_status(
        measurement_type="get_status",
        parameters={},
        status=stat.dict,
    )


@app.post(f"/{servKey}/get_meas_status")
async def get_meas_status():
    """Will return 'idle' or 'measuring'. Should be used in conjuction with eta to async.sleep loop poll"""
    return return_status(
        measurement_type="gamry_command",
    parameters={
        "command": "get_meas_status",
        "parameters": {},
    },
        status=await poti.status(),
    )


@app.post(f"/{servKey}/set_sample")
async def set_sample(
    samples: sample_class
):
    """setup the experiment desciption to be included in the output file"""
    await stat.set_run()
    poti.FIFO_sample = samples
    await stat.set_idle()

# these will work, but we should not call them alone 
# as it might cause issues if not done peroperly
# they will be called at the appropiate places in the other scripts
# I will leave them here just in case

# @app.post(f"/{servKey}/init_Gamry")
# async def init_Gamry():
#     """This will initialize the Gamry again in case connection was lost (will be done automatically when server starts)"""
#     await stat.set_run()

#     retc = return_class(
#         measurement_type="gamry_command",
#         parameters={
#             "command": "init_Gamry",
#             "parameters": {},
#         },
#         data=await poti.init_Gamry(poti.Gamry_devid)
#     )
#     await stat.set_idle()
#     return retc


# @app.post(f"/{servKey}/connection_open")
# async def connection_open():
#     """Opens a connection to the Gamry, needs to be done prior to any measurements"""
#     await stat.set_run()

#     retc = return_class(
#         measurement_type="gamry_command",
#         parameters={
#             "command": "connection_open",
#             "parameters": {},
#         },
#         data=await poti.open_connection()
#     )
#     await stat.set_idle()
#     return retc


# @app.post(f"/{servKey}/connection_close")
# async def connection_close():
#     """Closes a connection to the Gamry."""
#     await stat.set_run()

#     retc = return_class(
#         measurement_type="gamry_command",
#         parameters={
#             "command": "connection_close",
#             "parameters": {},
#         },
#         data=await poti.close_connection()
#     )
#     await stat.set_idle()
#     return retc


@app.post(f"/{servKey}/run_LSV")
async def run_LSV(
    Vinit: float = 0.0,         # Initial value in volts or amps.
    Vfinal: float = 1.0,        # Final value in volts or amps.
    ScanRate: float = 1.0,      # Scan rate in volts/second or amps/second.
    SampleRate: float = 0.01,   # Time between data acquisition samples in seconds.
    TTLwait: int = -1,          # -1 disables, else select TTL 0-3
    TTLsend: int = -1           # -1 disables, else select TTL 0-3
):
    """Linear Sweep Voltammetry (unlike CV no backward scan is done)"""
    await stat.set_run()
    retc = return_class(
    measurement_type="gamry_command",
    parameters={
        "command": "run_LSV",
        "parameters": {
            'Vinit':Vinit,
            'Vfinal':Vfinal,
            'scanrate':ScanRate,
            'samplerate':SampleRate
            },
    },
    data=await poti.technique_LSV(Vinit, Vfinal, ScanRate, SampleRate, TTLwait, TTLsend)
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_CA")
async def run_CA(
    Vval: float = 0.0,
    Tval: float = 10.0,
    SampleRate: float = 0.01,    # Time between data acquisition samples in seconds.
    TTLwait: int = -1, # -1 disables, else select TTL 0-3
    TTLsend: int = -1 # -1 disables, else select TTL 0-3
#    Vlimit: float = 10.0,
#    EQDelay: float = 5.0
):

    """Chronoamperometry (current response on amplied potential)"""
    await stat.set_run()
    retc = return_class(
    measurement_type="gamry_command",
    parameters={
        "command": "run_CA",
        "parameters": {
            'Vval': Vval,
            'Tval': Tval,
            'samplerate':SampleRate
            },
    },
    data=await poti.technique_CA(Vval, Tval, SampleRate, TTLwait, TTLsend)
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_CP")
async def run_CP(
    Ival: float = 0.0,
    Tval: float = 10.0,
    SampleRate: float = 1.0,      # Time between data acquisition samples in seconds.
    TTLwait: int = -1, # -1 disables, else select TTL 0-3
    TTLsend: int = -1 # -1 disables, else select TTL 0-3
#    Vlimit: float = 10.0,
#    EQDelay: float = 5.0
):
    """Chronopotentiometry (Potential response on controlled current)"""
    await stat.set_run()
    retc = return_class(
    measurement_type="gamry_command",
    parameters={
        "command": "run_CP",
        "parameters": {
            'Ival':Ival,
            'Tval':Tval,
            'samplerate':SampleRate
            },
    },
    data=await poti.technique_CP(Ival, Tval, SampleRate, TTLwait, TTLsend, TTLwait, TTLsend)
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_CV")
async def run_CV(
    Vinit: float = 0.0,           # Initial value in volts or amps.
    Vapex1: float = 1.0,          # Apex 1 value in volts or amps.
    Vapex2: float = -1.0,         # Apex 2 value in volts or amps.
    Vfinal: float = 0.0,          # Final value in volts or amps.
    ScanRate: float = 1.0,        # Apex scan rate in volts/second or amps/second.
    SampleRate: float = 0.01,     # Time between data acquisition steps.
    Cycles: int = 1,
    TTLwait: int = -1, # -1 disables, else select TTL 0-3
    TTLsend: int = -1 # -1 disables, else select TTL 0-3
):
    """Cyclic Voltammetry (most widely used technique for acquireing information about electrochemical reactions)"""
    await stat.set_run()
    retc = return_class(
    measurement_type="gamry_command",
    parameters={
        "command": "run_CV",
        "parameters": {},
    },
    # the cv can be more complex but we simply will use the same scanrates etc
    # technique_CV(self,
    #         Vinit: float,
    #         Vapex1: float,
    #         Vapex2: float,
    #         Vfinal: float,
    #         ScanInit: float,
    #         ScanApex: float,
    #         ScanFinal: float,
    #         HoldTime0: float,
    #         HoldTime1: float,
    #         HoldTime2: float,
    #         SampleRate: float,
    #         Cycles: int,
    #     ):
    data=await poti.technique_CV(
        Vinit,
        Vapex1,
        Vapex2,
        Vfinal,
        ScanRate,
        ScanRate,
        ScanRate,
        0.0,
        0.0,
        0.0,
        SampleRate,
        Cycles,
        TTLwait,
        TTLsend
        )
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc


@app.post(f"/{servKey}/run_EIS")
async def run_EIS(
    Vval: float = 0.0,
    Tval: float = 10.0,
    Freq: float = 1000.0,
    RMS: float = 0.02, 
    Precision: float = 0.001, #The precision is used in a Correlation Coefficient (residual power) based test to determine whether or not to measure another cycle.
    SampleRate: float = 0.01,
    TTLwait: int = -1, # -1 disables, else select TTL 0-3
    TTLsend: int = -1 # -1 disables, else select TTL 0-3
):
    """"""
    await stat.set_run()
    retc = return_class(
    measurement_type="gamry_command",
    parameters={
        "command": "run_EIS",
        "parameters": {
            'Vval':Vval,
            'Tval':Tval,
            'freq':Freq,
            'RMS':RMS,
            'precision':Precision,
            'samplerate':SampleRate
            },
    },
    data=await poti.technique_EIS(Vval, Tval, Freq, RMS, Precision, SampleRate, TTLwait, TTLsend) 
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc



@app.post(f"/{servKey}/run_OCV")
async def run_OCV(
    Tval: float = 10.0,
    SampleRate: float = 0.01,
    TTLwait: int = -1, # -1 disables, else select TTL 0-3
    TTLsend: int = -1 # -1 disables, else select TTL 0-3
):
    """"""
    await stat.set_run()
    retc = return_class(
    measurement_type="gamry_command",
    parameters={
        "command": "run_OCV",
        "parameters": {
            'Tval':Tval,
            'samplerate':SampleRate
                },
    },
    data=await poti.technique_OCV(Tval, SampleRate, TTLwait, TTLsend) 
    )
    # will be set within the driver
    #await stat.set_idle()
    return retc


@app.post(f"/{servKey}/stop")
async def stop():
    await stat.set_run()
    retc = return_class(
        #measurement_type="motion_command",
        #parameters={"command": "stop"},
        #data = motion.motor_off(motion.get_all_axis()),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/estop")
async def estop(switch: bool = True):
    await stat.set_run()
    retc = return_class(
        #measurement_type="motion_command",
        #parameters={"command": "estop", "parameters": switch},
        #data = motion.estop_axis(switch),
    )
    await stat.set_estop()
    return retc


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
def shutdown_event():
    # this gets called when the server is shut down or reloaded to ensure a clean
    # disconnect ... just restart or terminate the server
    asyncio.gather(poti.close_connection())
    poti.kill_GamryCom()
    return {"shutdown"}


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
