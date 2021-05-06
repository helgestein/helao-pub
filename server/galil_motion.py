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
from classes import wsConnectionManager
from classes import sample_class
from classes import transformxy

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]

app = FastAPI(title=servKey,
              description="Galil motion instrument/action server", version=1.0)

galil_motion_running = True



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
    instrxy = "instrxy"



@app.post(f"/{servKey}/setmotionref")
async def setmotionref():
    """Set the reference position for xyz by 
    (1) homing xyz, 
    (2) set abs zero, 
    (3) moving by center counts back, 
    (4) set abs zero"""
    await stat.set_run()
    # http://127.0.0.1:8001/motor/query/positions
    retc = return_class(
        measurement_type="motion_setref",
        parameters={"command": "setmotionref"},
        data=await motion.setaxisref()
    )
    await stat.set_idle()
    return retc



# parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(platexy).tolist())}
@app.post(f"/{servKey}/toMotorXY")
def transform_platexy_to_motorxy(platexy):
    """Converts plate to motor xy"""
    motorxy = motion.transform.transform_platexy_to_motorxy(json.loads(platexy))
    retc = return_class(
        measurement_type="motion_calculation",
        parameters={"command": "toMotorXY"},
        data={"motorxy":json.dumps(motorxy.tolist())}
    )
    return retc


# parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(motorxy).tolist())}
@app.post(f"/{servKey}/toPlateXY")
def transform_motorxy_to_platexy(motorxy):
    """Converts motor to plate xy"""
    platexy = motion.transform.transform_motorxy_to_platexy(json.loads(motorxy))
    retc = return_class(
        measurement_type="motion_calculation",
        parameters={"command": "toPlateXY"},
        data={"platexy":json.dumps(platexy.tolist())}
    )
    return retc


@app.post(f"/{servKey}/MxytoMPlate")
def MxytoMPlate(Mxy):
    """removes Minstr from Msystem to obtain Mplate for alignment"""
    Mplate = motion.transform.get_Mplate_Msystem(json.loads(Mxy))
    retc = return_class(
        measurement_type="motion_calculation",
        parameters={"command": "MxytoMPlate"},
        data={"Mplate":json.dumps(Mplate.tolist())}
    )
    return retc


@app.on_event("startup")
def startup_event():
    global motion
    motion = galil(S.params)
    global stat
    stat = StatusHandler()
    
    
    # if "M_instr" not in S.params:
    #     S.params["M_instr"] = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
    
    # global transform
    # transform = transformxy(S.params["M_instr"])

    
    global wsstatus
    wsstatus = wsConnectionManager()
    global wsdata
    wsdata = wsConnectionManager()


@app.websocket(f"/{servKey}/ws_motordata")
async def websocket_data(websocket: WebSocket):
    await wsdata.send(websocket, motion.qdata, 'galil_motion_data')


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.send(websocket, stat.q, 'galil_motion_status')


@app.post(f"/{servKey}/download_alignmentmatrix")
async def download_alignmentmatrix(newxyTransfermatrix):
    """Get current in use Alignment from motion server"""
    motion.transform.update_Mplatexy(json.loads(newxyTransfermatrix))


@app.post(f"/{servKey}/upload_alignmentmatrix")
async def upload_alignmentmatrix():
    """Send new Alignment to motion server"""
    return json.dumps(motion.transform.get_Mplatexy.tolist())


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
        


    # need to get absolute motor position first
    tmpmotorpos=await motion.query_axis_position(await motion.get_all_axis())
    print(' ... current absolute motor positions:',tmpmotorpos)
    # don't use dicts as we do math on these vectors
    current_positionvec = [0.0,0.0,0.0,0.0,0.0,0.0] # x, y, z, Rx, Ry, Rz
    # map the request to this
    req_positionvec = [0.0,0.0,0.0,0.0,0.0,0.0] # x, y, z, Rx, Ry, Rz


    reqdict = dict(zip(new_axis, new_d_mm))
    print(' ... requested position (',mode,'): ', reqdict)
    
    for idx, ax in enumerate(['x', 'y','z','Rx','Ry','Rz']):
        if ax in tmpmotorpos['ax']:
            # for current_positionvec
            current_positionvec[idx] = tmpmotorpos['position'][tmpmotorpos['ax'].index(ax)]
            # for req_positionvec
            if ax in reqdict:
                req_positionvec[idx] = reqdict[ax]

    print(' ... motor position vector:', current_positionvec[0:3])
    print(' ... requested position vector (',mode,')', req_positionvec)

    if transformation ==  transformation_mode.motorxy:
        # nothing to do
        print('motion: got motorxy, no transformation necessary')
    elif transformation ==  transformation_mode.platexy:
        print('motion: got platexy, converting to motorxy')
        motorxy = [0,0,1]
        motorxy[0] = current_positionvec[0]
        motorxy[1] = current_positionvec[1]
        current_platexy = motion.transform.transform_motorxy_to_platexy(motorxy)
            #transform.transform_motorxyz_to_instrxyz(current_positionvec[0:3])
        print(' ... current instrument position (calc from motor):', current_platexy)
        if mode == move_modes.relative:
            new_platexy = [0,0,1]
            new_platexy[0] = current_platexy[0]+req_positionvec[0]
            new_platexy[1] = current_platexy[1]+req_positionvec[1]
            print(' ... new platexy (abs)',new_platexy)
            new_motorxy =  motion.transform.transform_platexy_to_motorxy(new_platexy)
            print(' ... new motorxy (abs):',new_motorxy)
            new_axis = ['x', 'y']
            new_d_mm = [d for d in new_motorxy[0:2]]        
        elif mode == move_modes.absolute:
            new_platexy = [0,0,1]
            new_platexy[0] = req_positionvec[0]
            new_platexy[1] = req_positionvec[1]
            print(' ... new platexy (abs)',new_platexy)
            new_motorxy =  motion.transform.transform_platexy_to_motorxy(new_platexy)
            print(' ... new motorxy (abs):',new_motorxy)
            new_axis = ['x', 'y']
            new_d_mm = [d for d in new_motorxy[0:2]]

        elif mode == move_modes.homing:
            # not coordinate conversoion needed as these are not used (but length is still checked)
            pass


        xyvec = [0,0,1]
        for i, ax in enumerate(new_axis):
            if ax == 'x':
                xyvec[0] = new_d_mm[0]
            if ax == 'y':
                xyvec[1] = new_d_mm[1]
    elif transformation == transformation_mode.instrxy:
        print('motion: got instrxyz, converting to motorxy')
        current_instrxyz = motion.transform.transform_motorxyz_to_instrxyz(current_positionvec[0:3])
        print(' ... current instrument position (calc from motor):', current_instrxyz)
        if mode == move_modes.relative:
            new_instrxyz = current_instrxyz
            for i in range(3):
                new_instrxyz[i] = new_instrxyz[i]+req_positionvec[i]
            print(' ... new instrument position (abs):',new_instrxyz)
            # transform from instrxyz to motorxyz
            new_motorxyz =  motion.transform.transform_instrxyz_to_motorxyz(new_instrxyz[0:3])
            print(' ... new motor position (abs):',new_motorxyz)
            new_axis = ['x', 'y', 'z']
            new_d_mm = [d for d in new_motorxyz[0:3]]
            mode == move_modes.absolute
        elif mode == move_modes.absolute:
            print(' ... new instrument position (abs):',new_instrxyz)
            new_motorxyz =  motion.transform.transform_instrxyz_to_motorxyz(new_instrxyz[0:3])
            print(' ... new motor position (abs):',new_motorxyz)
            new_axis = ['x', 'y', 'z']
            new_d_mm = [d for d in new_motorxyz[0:3]]
        elif mode == move_modes.homing:
            # not coordinate conversoion needed as these are not used (but length is still checked)
            pass
        

    print(' ... final axis requested:',new_axis)
    print(' ... final d (',mode,') requested:', new_d_mm)


        
    
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
