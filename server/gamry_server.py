# shell: uvicorn motion_server:app --reload
""" A FastAPI service definition for a potentiostat device server, e.g. Gamry.

The potentiostat service defines RESTful methods for sending commmands and retrieving 
data from a potentiostat driver class such as 'gamry_driver' or 'gamry_simulate' using
FastAPI. The methods provided by this service are not device-specific. Appropriate code
must be written in the driver class to ensure that the service methods are generic, i.e.
calls to 'poti.*' are not device-specific. Currently inherits configuration from driver 
code, and hard-coded to use 'gamry' class (see "__main__").
"""

import os
import sys
import json
from importlib import import_module

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
# from gamry_simulate import gamry
from gamry_driver import gamry
confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


app = FastAPI(title=servKey,
              description="Gamry instrument/action server", version=1.0)


class return_class(BaseModel):
    measurement_type: str
    parameters: dict
    data: list
    

@app.on_event("startup")
def startup_event():
    global poti
    poti = gamry(S.params)


@app.websocket("/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await poti.q.get()
        data = {k: [v] for k, v in zip(["t_s", "Ewe_V", "Ach_V", "I_A"], data)}
        await websocket.send_text(json.dumps(poti.time_stamp))
        await websocket.send_text(json.dumps(data))


@app.post(f"/{servKey}/potential_ramp")
async def pot_potential_ramp_wrap(
    Vinit: float, Vfinal: float, ScanRate: float, SampleRate: float
):
    value = await poti.potential_ramp(Vinit, Vfinal, ScanRate, SampleRate)
    return return_class(**value)

@app.post(f"/{servKey}/potential_chrono_amp")
async def pot_chrono_amp_wrap(
    Vinit: float, Tinit: float, Vstep1: float, Tstep1: float, Vstep2: float, Tstep2: float, SampleRate: float 
):
    value = await poti.chrono_amp(Vinit, Tinit, Vstep1, Tstep1, Vstep2, Tstep2, SampleRate)
    return return_class(**value)

@app.post(f"/{servKey}/potential_chrono_pot")
async def pot_chrono_pot_wrap(
    Iinit: float, Tinit: float, Istep1: float, Tstep1: float, Istep2: float, Tstep2: float, SampleRate: float 
):
    value = await poti.chrono_pot(Iinit, Tinit, Istep1, Tstep1, Istep2, Tstep2, SampleRate)
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
    return return_class(**value)


# @app.post(f"/{servKey}/get/eis")
# async def eis_(start_freq: float, end_freq: float, points: int, pot_offset: float = 0):
#     return return_class(**poti.eis(start_freq, end_freq, points, pot_offset))


@app.post(f"/{servKey}/status")
def status_wrapper():
    return return_class(
        measurement_type="status_query",
        parameters={"query": "potentiostat"},
        data=[poti.status()],
    )


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
