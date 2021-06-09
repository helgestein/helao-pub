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
from enum import Enum
from importlib import import_module
import json

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify



helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))


from classes import move_modes
from typing import Optional
from prototyping import Action, HelaoFastAPI, Base

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
    print('Galil motion simulator loaded.')
    from galil_simulate import galil    
else:
    from galil_driver import galil

app = HelaoFastAPI(config, servKey, title=servKey,
              description="Galil motion instrument/action server", version=1.0)

galil_motion_running = True

class transformation_mode(str, Enum):
    motorxy = "motorxy"
    platexy = "platexy"
    instrxy = "instrxy"


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


@app.post(f"/{servKey}/setmotionref")
async def setmotionref(action_dict: Optional[dict]=None):
    """Set the reference position for xyz by 
    (1) homing xyz, 
    (2) set abs zero, 
    (3) moving by center counts back, 
    (4) set abs zero"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "setmotionref"
    active = await actserv.contain_action(A)
    await active.enqueue_data({"setref": await motion.setaxisref()})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


# parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(platexy).tolist())}
@app.post(f"/{servKey}/toMotorXY")
async def transform_platexy_to_motorxy(platexy: Optional[str]=None, action_dict: Optional[dict]=None):
    """Converts plate to motor xy"""
    if action_dict:
        A = Action(action_dict)
        platexy = A.action_params['platexy']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "toMotorXY"
        A.action_params['platexy'] = platexy
    active = await actserv.contain_action(A)
    motorxy = motion.transform.transform_platexy_to_motorxy(json.loads(platexy))
    await active.enqueue_data({"motorxy": json.dumps(motorxy.tolist())})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


# parse as {'M':json.dumps(np.matrix(M).tolist()),'platexy':json.dumps(np.array(motorxy).tolist())}
@app.post(f"/{servKey}/toPlateXY")
async def transform_motorxy_to_platexy(motorxy: Optional[str]=None, action_dict: Optional[dict]=None):
    """Converts motor to plate xy"""
    if action_dict:
        A = Action(action_dict)
        platexy = A.action_params['motorxy']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "toMotorXY"
        A.action_params['motorxy'] = motorxy
    active = await actserv.contain_action(A)
    platexy = motion.transform.transform_motorxy_to_platexy(json.loads(motorxy))
    await active.enqueue_data({"platexy": json.dumps(platexy.tolist())})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/MxytoMPlate")
async def MxytoMPlate(Mxy: Optional[str]=None, action_dict: Optional[dict]=None):
    """removes Minstr from Msystem to obtain Mplate for alignment"""
    if action_dict:
        A = Action(action_dict)
        Mxy = A.action_params['Mxy']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "MxytoMPlate"
        A.action_params['Mxy'] = Mxy
    active = await actserv.contain_action(A)
    Mplate = motion.transform.get_Mplate_Msystem(json.loads(Mxy))
    await active.enqueue_data({"Mplate": json.dumps(Mplate.tolist())})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/download_alignmentmatrix")
async def download_alignmentmatrix(newxyTransfermatrix: Optional[str]=None, action_dict: Optional[dict]=None):
    """Get current in use Alignment from motion server"""
    if action_dict:
        A = Action(action_dict)
        newxyTransfermatrix = A.action_params['newxyTransfermatrix']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "download_alignmentmatrix"
        A.action_params['newxyTransfermatrix'] = newxyTransfermatrix
    active = await actserv.contain_action(A)
    motion.transform.update_Mplatexy(json.loads(newxyTransfermatrix))
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/upload_alignmentmatrix")
async def upload_alignmentmatrix(action_dict: Optional[dict]=None):
    """Send new Alignment to motion server"""
    if action_dict:
        A = Action(action_dict)
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "download_alignmentmatrix"
    active = await actserv.contain_action(A)
    alignmentmatrix = json.dumps(motion.transform.get_Mplatexy.tolist())
    await active.enqueue_data({"alignmentmatrix": alignmentmatrix})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict


@app.post(f"/{servKey}/move")
async def move(
    d_mm: Optional[str]=None,
    axis: Optional[str]=None,
    speed: Optional[int]=None,
    mode: Optional[move_modes]="relative",
    transformation: Optional[transformation_mode]="motorxy", # default, nothing to do
    action_dict: Optional[dict]=None
):
    """Move a apecified {axis} by {d_mm} distance at {speed} using {mode} i.e. relative.
       Use Rx, Ry, Rz and not in combination with x,y,z only in motorxy.
       No z, Rx, Ry, Rz when platexy selected."""
    if action_dict:
        A = Action(action_dict)
        d_mm = A.action_params['d_mm']
        axis = A.action_params['axis']
        speed = A.action_params['speed']
        mode = A.action_params['mode']
        transformation = A.action_params['transformation']
    else:
        A = Action()
        A.action_server = servKey
        A.action_name = "move"
        A.action_params['d_mm'] = d_mm
        A.action_params['axis'] = axis
        A.action_params['speed'] = speed
        A.action_params['mode'] = mode
        A.action_params['transformation'] = transformation
    active = await actserv.contain_action(A)

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
#    req_positionvec = [0.0,0.0,0.0,0.0,0.0,0.0] # x, y, z, Rx, Ry, Rz
    req_positionvec = [None,None,None,None,None,None] # x, y, z, Rx, Ry, Rz


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
        print('motion: got motorxy (',mode,'), no transformation necessary')
    elif transformation ==  transformation_mode.platexy:
        print('motion: got platexy (',mode,'), converting to motorxy')
        motorxy = [0,0,1]
        motorxy[0] = current_positionvec[0]
        motorxy[1] = current_positionvec[1]
        current_platexy = motion.transform.transform_motorxy_to_platexy(motorxy)
            #transform.transform_motorxyz_to_instrxyz(current_positionvec[0:3])
        print(' ... current plate position (calc from motor):', current_platexy)
        if mode == move_modes.relative:
            new_platexy = [0,0,1]

            if req_positionvec[0] is not None:
                new_platexy[0] = current_platexy[0]+req_positionvec[0]
            else:
                new_platexy[0] = current_platexy[0]

            if req_positionvec[1] is not None:
                new_platexy[1] = current_platexy[1]+req_positionvec[1]
            else:
                new_platexy[1] = current_platexy[1]

            print(' ... new platexy (abs)',new_platexy)
            new_motorxy =  motion.transform.transform_platexy_to_motorxy(new_platexy)
            print(' ... new motorxy (abs):',new_motorxy)
            new_axis = ['x', 'y']
            new_d_mm = [d for d in new_motorxy[0:2]]        
            mode = move_modes.absolute
        elif mode == move_modes.absolute:
            new_platexy = [0,0,1]

            if req_positionvec[0] is not None:
                new_platexy[0] = req_positionvec[0]
            else:
                new_platexy[0] = current_platexy[0]

            if req_positionvec[1] is not None:
                new_platexy[1] = req_positionvec[1]
            else:
                new_platexy[1] = current_platexy[1]

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
        print(' ................mode', mode)
        print('motion: got instrxyz (',mode,'), converting to motorxy')
        current_instrxyz = motion.transform.transform_motorxyz_to_instrxyz(current_positionvec[0:3])
        print(' ... current instrument position (calc from motor):', current_instrxyz)
        if mode == move_modes.relative:
            new_instrxyz = current_instrxyz
            for i in range(3):
                if req_positionvec[i] is not None:
                    new_instrxyz[i] = new_instrxyz[i]+req_positionvec[i]
                else:
                    new_instrxyz[i] = new_instrxyz[i]
            print(' ... new instrument position (abs):',new_instrxyz)
            # transform from instrxyz to motorxyz
            new_motorxyz =  motion.transform.transform_instrxyz_to_motorxyz(new_instrxyz[0:3])
            print(' ... new motor position (abs):',new_motorxyz)
            new_axis = ['x', 'y', 'z']
            new_d_mm = [d for d in new_motorxyz[0:3]]
            mode = move_modes.absolute
        elif mode == move_modes.absolute:
            new_instrxyz = current_instrxyz
            for i in range(3):
                if req_positionvec[i] is not None:
                    new_instrxyz[i] = req_positionvec[i]
                else:
                    new_instrxyz[i] = new_instrxyz[i]
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

    return_data = await motion.motor_move(new_d_mm, new_axis, speed, mode)
    await active.enqueue_data({"return_data": return_data})
    finished_act = await active.finish()
    finished_dict = finished_act.as_dict()
    del finished_act
    return finished_dict
        

@app.post(f"/{servKey}/disconnect")
async def disconnect(action_dict: Optional[dict]=None):
    retc = return_class(
        measurement_type="motion_command",
        parameters={"command": "motor_disconnect_command"},
        data=await motion.motor_disconnect(),
    )
    return retc


@app.post(f"/{servKey}/query_positions")
async def query_positions(action_dict: Optional[dict]=None):
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
async def query_position(axis: Optional[str]=None, action_dict: Optional[dict]=None):
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
async def query_moving(axis: Optional[str]=None, action_dict: Optional[dict]=None):
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
async def axis_off(axis: Optional[str]=None, action_dict: Optional[dict]=None):
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
async def axis_on(axis: Optional[str]=None, action_dict: Optional[dict]=None):
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
async def stop(action_dict: Optional[dict]=None):
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
async def reset(action_dict: Optional[dict]=None):
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
async def estop(switch: Optional[bool]=True, action_dict: Optional[dict]=None):
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
    """Return a list of all endpoints on this server."""
    return actserv.get_endpoint_urls(app)


@app.post("/shutdown")
def post_shutdown():
    print(' ... motion shutdown ###')
    motion.shutdown_event()
#    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
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
