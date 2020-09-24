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
from galil_simulate import galil
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


@app.get(f"/{servKey}/query_analog_in")
def analog_in(port: int):
    # http://127.0.0.1:8001/io/query/analog_in?port=0
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_in"},
        data=motion.read_analog_in(port),
    )
    return retc


@app.get(f"/{servKey}/query_digital_in")
def digital_in(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_in"},
        data=motion.read_digital_in(port),
    )
    return retc


@app.get(f"/{servKey}/query_digital_out")
def read_digital_out(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.read_digital_out(port),
    )
    return retc


@app.get(f"/{servKey}/digital_out_on")
def read_digital_out(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.digital_out_on(port),
    )
    return retc


@app.get(f"/{servKey}/digital_out_off")
def read_digital_out(port: int):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.digital_out_off(port),
    )
    return retc


@app.get(f"/{servKey}/analog_out")
def set_analog_out(handle: int, module: int, bitnum: int, value: float):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.set_analog_out(handle, module, bitnum, value),
    )
    return retc


@app.get(f"/{servKey}/inf_digi_cycles")
def inf_cycles(time_on: float, time_off: float, port: int, init_time: float = 0.0):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.infinite_digital_cycles(time_off, time_on, port, init_time),
    )
    return retc


@app.get(f"/{servKey}/break_inf_digi_cycles")
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
    uvicorn.run(app, host=S.host, port=S.port)
