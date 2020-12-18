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
  await stat.update('busy', 'myprov')
and followed by :
  await stat.update('idle, 'myprov')
which will update this action server's status dictionary which is query-able via
../get_status, and also broadcast the status change via websocket ../ws_status

IMPORTANT -- this framework assumes a single data stream and structure produced by the
low level device driver, so ../ws_data will only broadcast the device class's  poti.q;
additional data streams may be added as separate websockets or reworked into present
../ws_data columar format with an additional tag column to differentiate streams

"""

import os
import sys
import json
from importlib import import_module
from asyncio import Queue
from time import strftime

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from classes import StatusHandler
confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


# check if 'simulate' settings is present
if not 'simulate' in S:
    # default if no simulate is defined
    print('"simulate" not defined, switching to Galil Simulator.')
    S['simulate']= False


if S.simulate:
    print('Gamry simulator loaded.')
    from gamry_simulate import gamry
else:
    from gamry_driver import gamry


app = FastAPI(title=servKey,
              description="Gamry instrument/action server", version=1.0)


class return_class(BaseModel):
    measurement_type: str
    parameters: dict
    data: list


class return_status(BaseModel):
    measurement_type: str
    parameters: dict
    status: dict
    

@app.on_event("startup")
def startup_event():
    global poti
    poti = gamry(S.params)
    global stat
    stat = StatusHandler()
    


# @app.websocket("/ws")
# async def websocket_messages(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await poti.q.get()
#         data = {k: [v] for k, v in zip(["t_s", "Ewe_V", "Ach_V", "I_A"], data)}
#         await websocket.send_text(json.dumps(poti.time_stamp))
#         await websocket.send_text(json.dumps(data))

@app.websocket(f"/{servKey}/ws_data")
async def websocket_data(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await poti.q.get()
        data = {k: [v] for k, v in zip(["t_s", "Ewe_V", "Ach_V", "I_A"], data)}
        await websocket.send_text(json.dumps(data))


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await stat.q.get()
        await websocket.send_text(json.dumps(data))
        
        
@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return return_status(
        measurement_type="get_status",
        parameters={},
        status=stat.dict,
    )

@app.post(f"/{servKey}/potential_ramp")
async def pot_potential_ramp_wrap(
    Vinit: float, Vfinal: float, ScanRate: float, SampleRate: float
):
    await stat.update('busy', 'myprov')
    value = await poti.potential_ramp(Vinit, Vfinal, ScanRate, SampleRate)
    await stat.update('idle', 'myprov')
    return return_class(**value)

@app.post(f"/{servKey}/potential_chrono_amp")
async def pot_chrono_amp_wrap(
    Vinit: float, Tinit: float, Vstep1: float, Tstep1: float, Vstep2: float, Tstep2: float, SampleRate: float 
):
    await stat.update('busy', 'myprov')
    value = await poti.chrono_amp(Vinit, Tinit, Vstep1, Tstep1, Vstep2, Tstep2, SampleRate)
    await stat.update('idle', 'myprov')
    return return_class(**value)

@app.post(f"/{servKey}/potential_chrono_pot")
async def pot_chrono_pot_wrap(
    Iinit: float, Tinit: float, Istep1: float, Tstep1: float, Istep2: float, Tstep2: float, SampleRate: float 
):
    await stat.update('busy', 'myprov')
    value = await poti.chrono_pot(Iinit, Tinit, Istep1, Tstep1, Istep2, Tstep2, SampleRate)
    await stat.update('idle', 'myprov')
    return return_class(**value)

@app.post(f"/{servKey}/potential_cycle")
async def pot_potential_cycle_wrap(
    Vinit: float,
    Vfinal: float,
    Vapex1: float,
    Vapex2: float,
    ScanRate: float,
    Cycles: int,
    SampleRate: float,
    control_mode: str,
):
    await stat.update('busy', 'myprov')
    value = await poti.potential_cycle(
        Vinit,
        Vfinal,
        Vapex1,
        Vapex2,
        ScanRate,
        Cycles,
        SampleRate,
        control_mode,
    )
    await stat.update('idle', 'myprov')
    return return_class(**value)


# @app.post(f"/{servKey}/get/eis")
# async def eis_(start_freq: float, end_freq: float, points: int, pot_offset: float = 0):
#     return return_class(**poti.eis(start_freq, end_freq, points, pot_offset))


# @app.post(f"/{servKey}/status")
# def status_wrapper():
#     return return_class(
#         measurement_type="status_query",
#         parameters={"query": "potentiostat"},
#         data=[poti.status()],
#     )


# @app.post(f"/{servKey}/get/signal_arr")
# async def signal_array_(Cycles: int, SampleRate: float, arr: str):
#     arr = [float(i) for i in arr.split(",")]
#     return return_class(**poti.signal_array(Cycles, SampleRate, arr))


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
    poti.close_connection()
    return {"shutdown"}


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
