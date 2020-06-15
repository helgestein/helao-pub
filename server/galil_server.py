# shell: uvicorn motion_server:app --reload

import os, sys

if __package__:
    # can import directly in package mode
    print("importing config vars from package path")
else:
    # interactive kernel mode requires path manipulation
    cwd = os.getcwd()
    pwd = os.path.dirname(cwd)
    print(pwd)
    if os.path.basename(pwd) == "HELAO":
        sys.path.insert(0, pwd)
    if pwd in sys.path or os.path.basename(cwd) == "HELAO":
        print("importing config vars from sys.path")
    else:
        raise ModuleNotFoundError("unable to find config vars, current working directory is {}".format(cwd))

from enum import Enum
import time
from fastapi import FastAPI
import uvicorn
# from galil_driver import *
from driver.galil_simulate import *
from pydantic import BaseModel

app = FastAPI()


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"


@app.get("/motor/set/move")
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


@app.get("/motor/set/move_live")
async def move_live(
    x_mm: float, axis: str, speed: int = None, mode: move_modes = "relative"
):
    """Move a apecified {axis} by {x_mm} distance at {speed} using {mode} i.e. relative"""
    # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x
    return StreamingResponse(
        motion.motor_move_live(x_mm, axis, speed, mode), media_type="text/plain"
    )


@app.get("/motor/set/disconnect")
def disconnect():
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_disconnect_command"},
        data=motion.motor_disconnect(),
    )
    return retc


@app.get("/motor/query/positions")
def query_positions():
    # http://127.0.0.1:8001/motor/query/positions
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_positions"},
        data=motion.query_all_axis_positions(),
    )
    return retc


@app.get("/motor/query/position")
def query_position(axis: str):
    # http://127.0.0.1:8001/motor/query/position?axis=x
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_position"},
        data=motion.query_axis(axis),
    )
    return retc


@app.get("/motor/query/moving")
def query_position(axis: str):
    # http://127.0.0.1:8001/motor/query/moving?axis=x
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_moving"},
        data=motion.query_moving(),
    )
    return retc


@app.get("/motor/set/off")
def axis_off(axis: str):
    # http://127.0.0.1:8001/motor/set/off?axis=x
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_off", "parameters": {"axis": axis}},
        data=motion.motor_off(axis),
    )
    return retc


@app.get("/motor/set/on")
def axis_on(axis: str):
    # http://127.0.0.1:8001/motor/set/on?axis=x
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_off", "parameters": {"axis": axis}},
        data=motion.motor_on(axis),
    )
    return retc


@app.get("/motor/set/stop")
def stop():
    # http://127.0.0.1:8001/motor/set/stop
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "stop"},
        data=motion.motor_stop(),
    )
    return retc


@app.get("/io/query/analog_in")
def analog_in(port: int):
    # http://127.0.0.1:8001/io/query/analog_in?port=0
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_in"},
        data=motion.read_analog_in(port),
    )
    return retc


@app.get("/io/query/digital_in")
def digital_in(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_in"},
        data=motion.read_digital_in(port),
    )
    return retc


@app.get("/io/query/digital_out")
def read_digital_out(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.read_digital_out(port),
    )
    return retc


@app.get("/io/set/digital_out_on")
def read_digital_out(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.digital_out_on(port),
    )
    return retc


@app.get("/io/set/digital_out_off")
def read_digital_out(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.digital_out_off(port),
    )
    return retc


@app.get("/io/set/analog_out")
def set_analog_out(handle: int, module: int, bitnum: int, value: float):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.set_analog_out(handle, module, bitnum, value),
    )
    return retc


@app.get("/io/set/inf_digi_cycles")
def inf_cycles(time_on: float, time_off: float, port: int, init_time: float = 0.0):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.infinite_digital_cycles(time_off, time_on, port, init_time),
    )
    return retc


@app.get("/io/set/break_inf_digi_cycles")
def break_inf_cycles():
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.break_infinite_digital_cycles(),
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
    # makes this runnable and debuggable in VScode
    # letters of the alphabet GALIL => G6 A0 L11 I8 L11
    motion = galil()
    uvicorn.run(app, host=FASTAPI_HOST, port=MOTION_PORT)
