# shell: uvicorn motion_server:app --reload
""" A FastAPI service definition for a motion/IO server, e.g. Galil.

The motion/IO service defines RESTful methods for sending commmands and retrieving data
from a motion controller driver class such as 'galil_driver' or 'galil_simulate' using
FastAPI. The methods provided by this service are not device-specific. Appropriate code
must be written in the driver class to ensure that the service methods are generic, i.e.
calls to 'motion.*' are not device-specific. Currently inherits configuration from
driver code, and hard-coded to use 'galil' class (see "__main__").
"""

import os
import sys
#import time
from enum import Enum
from importlib import import_module
import json

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from munch import munchify
from starlette.responses import StreamingResponse


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

app = FastAPI(title=servKey,
              description="Galil motion instrument/action server", version=1.0)


# check if 'simulate' settings is present
if not 'simulate' in S:
    # default if no simulate is defined
    print('"simulate" not defined, switching to Galil Simulator.')
    S['simulate']= False
if S.simulate:
    print('Galil motion simulator loaded.')
    from galil_simulate import galil    
else:
    from galil_driver import galil


class return_status(BaseModel):
    measurement_type: str
    parameters: dict
    status: dict

@app.on_event("startup")
def startup_event():
    global motion
    motion = galil(S.params)
    global stat
    stat = StatusHandler()
    

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

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"


@app.post(f"/{servKey}/move")
async def move(
    x_mm: str,
    axis: str,
    speed: int = None,
    mode: move_modes = "relative"
):
    """Move a apecified {axis} by {x_mm} distance at {speed} using {mode} i.e. relative"""
    await stat.set_run()
    # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x
    stopping=False
    # TODO: no same axis in sequence
    
    # for multi axis movement, we need to split x_mm and axis into lists
    # (1) find separator and split it, else assume single axis move
    sepvals = [' ',',','\t',';','::',':']
    new_axis = None
    new_x_mm = None

    
    for sep in sepvals:
        if not (x_mm.find(sep) == -1) and not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                new_x_mm = [float(item) for item in x_mm.split(sep)]
                break
    
    # single axis
    if new_x_mm == None:
        new_axis = axis
        new_x_mm = float(x_mm)
   
    
    retc = return_class(
        measurement_type="motion_command",
        parameters={
            "command": "move_axis",
            "parameters": {
                "x_mm": new_x_mm,
                "axis": new_axis,
                "speed": speed,
                "mode": mode,
                "stopping": stopping,
            },
        },
        data=motion.motor_move(new_x_mm, new_axis, speed, mode),
    )

    # check for errors    
    if all(retc.data['err_code']):
        await stat.set_error()
    else:
        await stat.set_idle()

    return retc


@app.post(f"/{servKey}/move_live")
async def move_live(
    x_mm: float, axis: str, speed: int = None, mode: move_modes = "relative"
):
    """Move a specified {axis} by {x_mm} distance at {speed} using {mode} i.e. relative"""
    # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x

    # value = motion.motor_move_live(x_mm, axis, speed, mode)
    # return return_class(value)

    return StreamingResponse(
        motion.motor_move_live(x_mm, axis, speed, mode), media_type="text/plain"
    )


@app.post(f"/{servKey}/disconnect")
def disconnect():
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_disconnect_command"},
        data=motion.motor_disconnect(),
    )
    return retc


@app.post(f"/{servKey}/query_positions")
def query_positions():
    # http://127.0.0.1:8001/motor/query/positions
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_positions"},
        data=motion.query_axis_position(motion.get_all_axis())
    )
    return retc


@app.post(f"/{servKey}/query_position")
def query_position(axis: str):
    # http://127.0.0.1:8001/motor/query/position?axis=x

    sepvals = [' ',',','\t',';','::',':']
    new_axis = None
    for sep in sepvals:
        if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break    
    # single axis
    if new_axis == None:
        new_axis = axis

    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_position", "parameters": {"axis": new_axis}},
        data=motion.query_axis_position(new_axis),
    )
    return retc


@app.post(f"/{servKey}/query_moving")
def query_moving(axis: str):
    # http://127.0.0.1:8001/motor/query/moving?axis=x

    sepvals = [' ',',','\t',';','::',':']
    new_axis = None
    for sep in sepvals:
        if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break    
    # single axis
    if new_axis == None:
        new_axis = axis

    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_axis_moving", "parameters": {"axis": new_axis}},
        data=motion.query_axis_moving(),
    )
    return retc


@app.post(f"/{servKey}/off")
def axis_off(axis: str):
    # http://127.0.0.1:8001/motor/set/off?axis=x
    
    sepvals = [' ',',','\t',';','::',':']
    new_axis = None
    for sep in sepvals:
        if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break    
    # single axis
    if new_axis == None:
        new_axis = axis
        
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_off", "parameters": {"axis": new_axis}},
        data=motion.motor_off(new_axis),
    )
    return retc


@app.post(f"/{servKey}/on")
def axis_on(axis: str):
    # http://127.0.0.1:8001/motor/set/on?axis=x

    sepvals = [' ',',','\t',';','::',':']
    new_axis = None
    for sep in sepvals:
        if not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                break    
    # single axis
    if new_axis == None:
        new_axis = axis

    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_on", "parameters": {"axis": new_axis}},
        data=motion.motor_on(new_axis),
    )
    return retc


@app.post(f"/{servKey}/stop")
def stop():
    # http://127.0.0.1:8001/motor/set/stop
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "stop"},
        data = motion.motor_off(motion.get_all_axis()),
    )
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
def shutdown():
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "shutdown"},
        data=motion.shutdown_event(),
    )
    return retc


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
