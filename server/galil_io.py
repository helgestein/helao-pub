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
#from enum import Enum
from importlib import import_module
import json

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
from classes import return_status
from classes import return_class
from classes import wsConnectionManager

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
    print('Galil I/O simulator loaded.')
    from galil_simulate import galil    
else:
    from galil_driver import galil


app = FastAPI(title=servKey,
              description="Galil I/O instrument/action server", version=1.0)


@app.on_event("startup")
def startup_event():
    global motion
    motion = galil(S.params)
    global stat
    stat = StatusHandler()
    global wsstatus
    wsstatus = wsConnectionManager()


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.send(websocket, stat.q, 'IO_status')
        

@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return stat.dict()


@app.post(f"/{servKey}/query_analog_in")
def read_analog_in(port, action_params = ''):

    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)


    # http://127.0.0.1:8001/io/query/analog_in?port=0
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_in"},
        data=motion.read_analog_in(new_port),
    )
    return retc


@app.post(f"/{servKey}/query_digital_in")
def read_digital_in(port, action_params = ''):

    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)

    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_in"},
        data=motion.read_digital_in(new_port),
    )
    return retc


@app.post(f"/{servKey}/query_digital_out")
def read_digital_out(port, action_params = ''):

    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)

    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.read_digital_out(new_port),
    )
    return retc


@app.post(f"/{servKey}/digital_out_on")
def set_digital_out_on(port, action_params = ''):
    
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.digital_out_on(new_port),
    )
    return retc


@app.post(f"/{servKey}/digital_out_off")
def set_digital_out_off(port, action_params = ''):
    
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    
    
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "digital_out_query"},
        data=motion.digital_out_off(new_port),
    )
    return retc


@app.post(f"/{servKey}/set_triggered_cycles")
def set_triggered_cycles(trigger_port: int, out_port: int, t_cycle: int, action_params = ''):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "set_digital_cycle"},
        data=motion.set_digital_cycle(trigger_port, out_port, t_cycle)
    )
    return retc


@app.post(f"/{servKey}/analog_out")
def set_analog_out(port: int, value: float, action_params = ''):
#def set_analog_out(handle: int, module: int, bitnum: int, value: float):
    # TODO
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.set_analog_out(port, value),
        #data=motion.set_analog_out(handle, module, bitnum, value),
    )
    return retc


@app.post(f"/{servKey}/inf_digi_cycles")
def inf_cycles(time_on: float, time_off: float, port: int, init_time: float = 0.0, action_params = ''):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.infinite_digital_cycles(time_off, time_on, port, init_time),
    )
    return retc


@app.post(f"/{servKey}/break_inf_digi_cycles")
def break_inf_cycles(action_params = ''):
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "analog_out_set"},
        data=motion.break_infinite_digital_cycles(),
    )
    return retc


@app.post(f"/{servKey}/reset")
async def reset(action_params = ''):
    """Resets Galil device. Only for emergency use!"""
    await stat.set_run()
    retc = return_class(
        measurement_type="io_command",
        parameters={"command": "reset"},
        data = motion.reset(),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/estop")
async def estop(switch: bool = True, action_params = ''):
    # http://127.0.0.1:8001/motor/set/stop
    await stat.set_run()
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "estop", "parameters": switch},
        data = motion.estop_io(switch),
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


@app.post("/shutdown")
def post_shutdown():
    pass
#    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "shutdown"},
        data=motion.shutdown_event(),
    )
    return retc


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
