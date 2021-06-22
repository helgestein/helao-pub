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
from typing import Optional
from importlib import import_module

import uvicorn
from fastapi import WebSocket
from munch import munchify

# helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# sys.path.append(os.path.join(helao_root, 'config'))
# sys.path.append(os.path.join(helao_root, 'driver'))
# sys.path.append(os.path.join(helao_root, 'core'))

from ..core.servers import Action, HelaoFastAPI, Base

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


app = HelaoFastAPI(config, servKey, title=servKey,
              description="Galil I/O instrument/action server", version=1.0)


@app.on_event("startup")
def startup_event():
    global motion
    motion = galil(S.params)
    global actserv
    actserv = Base(app)

@app.websocket(f"/ws_status")
async def websocket_status(websocket: WebSocket):
    """Broadcast status messages.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await actserv.ws_status(websocket)


@app.websocket(f"/ws_data")
async def websocket_data(websocket: WebSocket):
    """Broadcast status dicts.

    Args:
      websocket: a fastapi.WebSocket object
    """
    await actserv.ws_data(websocket)
    

@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return actserv.status


@app.post(f"/{servKey}/query_analog_in")
async def read_analog_in(port: Optional[int]=None, action_dict: Optional[dict]=None):
    # http://127.0.0.1:8001/io/query/analog_in?port=0
    if action_dict:
        A = Action(action_dict)
        port = A.action_params['port']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "query_analog_in"
        A.action_params['port'] = port
    active = await actserv.contain_action(A)
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    await active.enqueue_data({"analog_in": motion.read_analog_in(new_port)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/query_digital_in")
async def read_digital_in(port: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        port = A.action_params['port']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "query_digital_in"
        A.action_params['port'] = port
    active = await actserv.contain_action(A)
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    await active.enqueue_data({"digital_in": motion.read_digital_in(new_port)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/query_digital_out")
async def read_digital_out(port: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        port = A.action_params['port']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "query_digital_out"
        A.action_params['port'] = port
    active = await actserv.contain_action(A)
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    await active.enqueue_data({"digital_out": motion.read_digital_out(new_port)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/digital_out_on")
async def set_digital_out_on(port: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        port = A.action_params['port']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "digital_out_on"
        A.action_params['port'] = port
    active = await actserv.contain_action(A)
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    await active.enqueue_data({"digital_out_on": motion.digital_out_on(new_port)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/digital_out_off")
async def set_digital_out_off(port: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        port = A.action_params['port']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "digital_out_off"
        A.action_params['port'] = port
    active = await actserv.contain_action(A)
    sepvals = [' ',',','\t',';','::',':']
    new_port = None
    for sep in sepvals:
        if not (port.find(sep) == -1):
                new_port = [int(item) for item in port.split(sep)]
                break    
    # single port
    if new_port == None:
        new_port = int(port)
    await active.enqueue_data({"digital_out_off": motion.digital_out_off(new_port)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/set_triggered_cycles")
async def set_triggered_cycles(trigger_port: Optional[int]=None, out_port: Optional[int]=None, t_cycle: Optional[int]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        trigger_port = A.action_params['trigger_port']
        out_port = A.action_params['out_port']
        t_cycle = A.action_params['t_cycle']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "set_triggered_cycles"
        A.action_params['trigger_port'] = trigger_port
        A.action_params['out_port'] = out_port
        A.action_params['t_cycle'] = t_cycle
    active = await actserv.contain_action(A)
    await active.enqueue_data({"digital_cycle": motion.set_digital_cycle(trigger_port, out_port, t_cycle)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/analog_out")
async def set_analog_out(port: Optional[int]=None, value: Optional[float]=None, action_dict: Optional[dict]=None):
#async def set_analog_out(handle: int, module: int, bitnum: int, value: float):
    # TODO
    if action_dict:
        A = Action(action_dict)
        port = A.action_params['port']
        value = A.action_params['value']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "analog_out"
        A.action_params['port'] = port
        A.action_params['value'] = value
    active = await actserv.contain_action(A)
    await active.enqueue_data({"analog_out": motion.set_analog_out(port, value)})
    # await active.enqueue_data({"analog_out": motion.set_analog_out(handle, module, bitnum, value)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/inf_digi_cycles")
async def inf_cycles(time_on: Optional[float]=None, time_off: Optional[float]=None, port: Optional[int]=None, init_time: Optional[float]=None, action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
        time_on = A.action_params['time_on']
        time_off = A.action_params['time_off']
        port = A.action_params['port']
        init_time = A.action_params['init_time']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "inf_digi_cycles"
        A.action_params['time_on'] = time_on 
        A.action_params['time_off'] = time_off 
        A.action_params['port'] = port 
        A.action_params['init_time'] = init_time 
    active = await actserv.contain_action(A)
    await active.enqueue_data({"analog_out": motion.infinite_digital_cycles(time_off, time_on, port, init_time)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/break_inf_digi_cycles")
async def break_inf_cycles(action_dict: Optional[dict]=None):
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "break_inf_digi_cycles"
    active = await actserv.contain_action(A)
    await active.enqueue_data({"analog_out": motion.break_infinite_digital_cycles()})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servkey}/reset")
async def reset(action_dict: optional[dict]=none):
    """resets galil device. only for emergency use!"""
    if action_dict:
        a = action(action_dict)
    else:
        a = action()
        a.action_server = servkey
        a.action_name = "reset"
    active = await actserv.contain_action(a)
    await active.enqueue_data({"reset": await motion.reset()})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/estop")
async def estop(switch: Optional[bool]=True, action_dict: Optional[dict]=None):
    # http://127.0.0.1:8001/motor/set/stop
    if action_dict:
        A = Action(action_dict)
        switch = A.action_params['switch']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "estop"
        A.action_params['switch']
    active = await actserv.contain_action(A)
    await active.enqueue_data({"estop": await motion.estop_io(switch)})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post('/endpoints')
def get_all_urls():
    """Return a list of all endpoints on this server."""
    return actserv.get_endpoint_urls(app)


@app.post("/shutdown")
def post_shutdown():
    pass
#    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
    motion.shutdown_event()


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
