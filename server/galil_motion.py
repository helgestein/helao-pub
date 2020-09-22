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
import time
from enum import Enum
from importlib import import_module


import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
from galil_simulate import *
confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]

app = FastAPI()


@app.on_event("startup")
def startup_event():
    global motion
    motion = galil(S.params)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"


@app.get(f"/{servKey}/move")
def move(
    x_mm: float,
    axis: str,
    speed: int = None,
    mode: move_modes = "relative",
    stopping: bool = True,
):
    """Move a apecified {axis} by {x_mm} distance at {speed} using {mode} i.e. relative"""
    # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x

    # stopping is currently not working ... calling two motors at the same time will stop one motion
    retc = return_class(
        measurement_type="motion_command",
        parameters={
            "command": "move_axis",
            "parameters": {
                "x_mm": x_mm,
                "axis": axis,
                "speed": speed,
                "mode": mode,
                "stopping": stopping,
            },
        },
        data=motion.motor_move(x_mm, axis, speed, mode),
    )
    return retc


from starlette.responses import StreamingResponse


@app.get(f"/{servKey}/move_live")
async def move_live(
    x_mm: float, axis: str, speed: int = None, mode: move_modes = "relative"
):
    """Move a apecified {axis} by {x_mm} distance at {speed} using {mode} i.e. relative"""
    # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x

    # value = motion.motor_move_live(x_mm, axis, speed, mode)
    # return return_class(value)

    return StreamingResponse(
        motion.motor_move_live(x_mm, axis, speed, mode), media_type="text/plain"
    )


@app.get(f"/{servKey}/disconnect")
def disconnect():
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_disconnect_command"},
        data=motion.motor_disconnect(),
    )
    return retc


@app.get(f"/{servKey}/query_positions")
def query_positions():
    # http://127.0.0.1:8001/motor/query/positions
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_positions"},
        data=motion.query_all_axis_positions(),
    )
    return retc


@app.get(f"/{servKey}/query_position")
def query_position(axis: str):
    # http://127.0.0.1:8001/motor/query/position?axis=x
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_position"},
        data=motion.query_axis(axis),
    )
    return retc


@app.get(f"/{servKey}/query_moving")
def query_position(axis: str):
    # http://127.0.0.1:8001/motor/query/moving?axis=x
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_moving"},
        data=motion.query_moving(),
    )
    return retc


@app.get(f"/{servKey}/off")
def axis_off(axis: str):
    # http://127.0.0.1:8001/motor/set/off?axis=x
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_off", "parameters": {"axis": axis}},
        data=motion.motor_off(axis),
    )
    return retc


@app.get(f"/{servKey}/on")
def axis_on(axis: str):
    # http://127.0.0.1:8001/motor/set/on?axis=x
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_off", "parameters": {"axis": axis}},
        data=motion.motor_on(axis),
    )
    return retc


@app.get(f"/{servKey}/stop")
def stop():
    # http://127.0.0.1:8001/motor/set/stop
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "stop"},
        data=motion.motor_stop(),
    )
    return retc


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
