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
import json
import asyncio

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify
import numpy as np
#from starlette.responses import StreamingResponse
#import copy
#import uuid

#from websockets import WebSocket


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))


from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import move_modes


confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]

app = FastAPI(title=servKey,
              description="Galil motion instrument/action server", version=1.0)

galil_motion_running = True


# local buffer of motor websocket data
motor_wsdata = []
# timecode for last ws data fetch
motor_wsdata_TC = 0

xyTransfermatrix = np.matrix([[0.5,0,10],[0,0.5,20],[0,0,1]])


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


class transformation_mode(str, Enum):
    motorxy = "motorxy"
    platexy = "platexy"


# parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(platexy).tolist())}
@app.post(f"/{servKey}/toMotorXY")
def transform_platexy_to_motorxy(M, platexy):
    """Converts plate to motor xy"""
    # M is Transformation matrix from plate to motor
    #motor = M*plate
    motorxy = np.dot(np.asmatrix(json.loads(M)),np.asarray(json.loads(platexy)))
    retc = return_class(
        measurement_type="motion_calculation",
        parameters={"command": "toMotorXY"},
        data={"MotorXY":json.dumps(np.asarray(motorxy)[0].tolist())}
    )
    return retc


# parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(motorxy).tolist())}
@app.post(f"/{servKey}/toPlateXY")
def transform_motorxy_to_platexy(M, motorxy):
    """Converts motor to plate xy"""
    # M is Transformation matrix from plate to motor
    #motor = M*plate
    #Minv*motor = Minv*M*plate = plate
    print(np.asarray(json.loads(motorxy)))
    print(M)
    try:
        platexy = np.dot(np.asmatrix(json.loads(M)).I,np.asarray(json.loads(motorxy)))         
    except Exception:
        print('------------------------------ Matrix singular ---------------------------')
        platexy = np.array([[None, None, None]])
    retc = return_class(
        measurement_type="motion_calculation",
        parameters={"command": "toPlateXY"},
        data={"PlateXY":json.dumps(np.asarray(platexy)[0].tolist())}
    )
    return retc


@app.on_event("startup")
def startup_event():
    global motion
    motion = galil(S.params)
    global stat
    stat = StatusHandler()

    myloop = asyncio.get_event_loop()
    #add websocket IO loop
    myloop.create_task(wsdata_IOloop())


async def wsdata_IOloop():
    global motor_wsdata_TC, motor_wsdata
    global galil_motion_running
    global xyTransfermatrix
    while galil_motion_running:
        try:
            motor_wsdata = await motion.ws_getmotordata()
            # add some extra data
            if 'x' in motor_wsdata['axis']:
                idx = motor_wsdata['axis'].index('x')
                xmotor = motor_wsdata['position'][idx]
            else:
                xmotor = None
        
            if 'y' in motor_wsdata['axis']:
                idx = motor_wsdata['axis'].index('y')
                ymotor = motor_wsdata['position'][idx]
            else:
                ymotor = None
            retval = transform_motorxy_to_platexy(json.dumps(xyTransfermatrix.tolist()), json.dumps(np.array([xmotor, ymotor, 1]).tolist()))
            platexy = np.asarray(json.loads(retval.data['PlateXY']))
            motor_wsdata['PlateXY'] = [platexy[0], platexy[0], 1]
            motor_wsdata_TC = time.time_ns()
        except Exception:
            print('Connection to motor unexpectedly lost. Retrying in 3 seconds.')
            await asyncio.sleep(3)


# stream the a buffered version
# buffer will be updated by all regular queries
# don't use for critical application, the low broadcast frequency can miss events
@app.websocket(f"/{servKey}/ws_motordata")
async def websocket_data(mywebsocket: WebSocket):  
    await mywebsocket.accept()
    global motor_wsdata_TC, motor_wsdata
    # local timecode to check against buffered data timecode
    localTC = 0
    while galil_motion_running:
        try:
            if localTC < motor_wsdata_TC:
                localTC = motor_wsdata_TC
                await mywebsocket.send_text(json.dumps(motor_wsdata))
            await asyncio.sleep(1)
        except WebSocket.exceptions.ConnectionClosedError:
                print('Websocket connection unexpectedly closed. Retrying in 3 seconds.')
                await asyncio.sleep(3)


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    while galil_motion_running:
        data = await stat.q.get()
        await websocket.send_text(json.dumps(data))


@app.post(f"/{servKey}/upload_alignmentmatrix")
async def upload_alignmentmatrix(newxyTransfermatrix):
    """Get current in use Alignment from motion server"""
    global xyTransfermatrix
    xyTransfermatrix = np.asmatrix(json.loads(newxyTransfermatrix))


@app.post(f"/{servKey}/download_alignmentmatrix")
async def download_alignmentmatrix():
    """Send new Alignment to motion server"""
    global xyTransfermatrix
    return json.dumps(xyTransfermatrix.tolist())


@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return return_status(
        measurement_type="get_status",
        parameters={},
        status=stat.dict,
    )


@app.post(f"/{servKey}/move")
async def move(
    d_mm: str,
    axis: str,
    speed: int = None,
    mode: move_modes = "relative",
    transformation: transformation_mode = "motorxy" # default, nothing to do
):
    """Move a apecified {axis} by {d_mm} distance at {speed} using {mode} i.e. relative"""
    await stat.set_run()
    # http://127.0.0.1:8001/motor/set/move?d_mm=-20&axis=x
    stopping=False
    # TODO: no same axis in sequence
    
    # for multi axis movement, we need to split d_mm and axis into lists
    # (1) find separator and split it, else assume single axis move
    sepvals = [' ',',','\t',';','::',':']
    new_axis = None
    new_d_mm = None

    for sep in sepvals:
        if not (d_mm.find(sep) == -1) and not (axis.find(sep) == -1):
                new_axis = axis.split(sep)
                new_d_mm = [float(item) for item in d_mm.split(sep)]
                break
    
    # single axis
    if new_d_mm == None:
        new_axis = axis
        new_d_mm = float(d_mm)

    # convert single axis move to list        
    if type(new_d_mm) is not list:
        new_axis = [new_axis]
        new_d_mm = [new_d_mm]

    transformation = "motorxy"
    if transformation == "motorxy":
        # nothing to do
        print('motion: got motorxy')
    if transformation == "platexy":
        print('motion: got platexy, converting to motorxy')
        xyvec = [0,0,1]
        for i, ax in enumerate(new_axis):
            if ax == 'x':
                xyvec[0] = new_d_mm[0]
            if ax == 'y':
                xyvec[1] = new_d_mm[1]
        # need to check if absolute or relative
        # transformation works on absolute coordinates
        #coordinates are given in plate xy system
        print(xyvec)
        new_xyvec=transform_platexy_to_motorxy(xyTransfermatrix, xyvec)
        print(new_xyvec)
#        mode = "absolute"
        
    
    retc = return_class(
        measurement_type="motion_command",
        parameters={
            "command": "move_axis",
            "parameters": {
                "d_mm": new_d_mm,
                "axis": new_axis,
                "speed": speed,
                "mode": mode,
                "stopping": stopping,
            },
        },
        data=await motion.motor_move(new_d_mm, new_axis, speed, mode),
    )

    # check for errors    
    if all(retc.data['err_code']):
        await stat.set_error()
    else:
        await stat.set_idle()

    return retc


# @app.post(f"/{servKey}/move_live")
# async def move_live(
#     d_mm: float, axis: str, speed: int = None, mode: move_modes = "relative"
# ):
#     """Move a specified {axis} by {d_mm} distance at {speed} using {mode} i.e. relative"""
#     # http://127.0.0.1:8001/motor/set/move?d_mm=-20&axis=x

#     # value = motion.motor_move_live(d_mm, axis, speed, mode)
#     # return return_class(value)

#     return StreamingResponse(
#         motion.motor_move_live(d_mm, axis, speed, mode), media_type="text/plain"
#     )


@app.post(f"/{servKey}/disconnect")
async def disconnect():
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_disconnect_command"},
        data=await motion.motor_disconnect(),
    )
    return retc


@app.post(f"/{servKey}/query_positions")
async def query_positions():
    await stat.set_run()
    # http://127.0.0.1:8001/motor/query/positions
    retc = return_class(
        measurement_type="motion_query",
        parameters={"command": "query_positions"},
        data=await motion.query_axis_position(await motion.get_all_axis())
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/query_position")
async def query_position(axis: str):
    # http://127.0.0.1:8001/motor/query/position?axis=x
    await stat.set_run()
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
        data=await motion.query_axis_position(new_axis),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/query_moving")
async def query_moving(axis: str):
    # http://127.0.0.1:8001/motor/query/moving?axis=x
    await stat.set_run()
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
        data=await motion.query_axis_moving(new_axis),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/off")
async def axis_off(axis: str):
    # http://127.0.0.1:8001/motor/set/off?axis=x
    await stat.set_run()
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
        data=await motion.motor_off(new_axis),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/on")
async def axis_on(axis: str):
    # http://127.0.0.1:8001/motor/set/on?axis=x
    await stat.set_run()
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
        data=await motion.motor_on(new_axis),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/stop")
async def stop():
    await stat.set_run()
    # http://127.0.0.1:8001/motor/set/stop
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "stop"},
        data = await motion.motor_off(await motion.get_all_axis()),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/reset")
async def reset():
    """Resets Galil device. Only for emergency use!"""
    await stat.set_run()
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "reset"},
        data = await motion.reset(),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/estop")
async def estop(switch: bool = True):
    # http://127.0.0.1:8001/motor/set/stop
    await stat.set_run()
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "estop", "parameters": switch},
        data = await motion.estop_axis(switch),
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
def shutdown():
    global galil_motion_running
    galil_motion_running = False
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "shutdown"},
        data=motion.shutdown_event(),
    )
    return retc


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
