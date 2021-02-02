# Instrument Alignment server
# talks with specified motor server and provides input to separate user interface server

# TODO: add checks against align.aligning

import os
import sys

from importlib import import_module
import json
import uvicorn

from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from munch import munchify

import requests
import asyncio
#import aiohttp
from enum import Enum


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))
from classes import StatusHandler


################## Helper functions ##########################################
# this could also move into a separate driver, but should not be necessary
# as all of this can also be in the FastAPI functions itself

class aligner:
    def __init__(self, config_dict, C):
        self.config_dict = config_dict
        self.C = C
        # determines if an alignment is currently running
        # needed for visualizer
        # to signal end of alignment
        self.aligning = False
        # default instrument specific Transfermatrix
        self.Transfermatrix = config_dict['Transfermatrix']
        # for saving Transfermatrix
        self.newTransfermatrix = config_dict['Transfermatrix']
        # for saving errorcode
        self.errorcode = 0

        # TODO: Need to be replaced later for ORCH call, instead direct call
        self.motorserv = config_dict['motor_server']
        self.motorhost = C[self.motorserv].host
        self.motorport = C[self.motorserv].port

        self.visserv = config_dict['vis_server']
        self.vishost = C[self.visserv].host
        self.visport = C[self.visserv].port

        # TODO: need another way to get which data_server to use?
        # do this via orch call later
        self.dataserv = config_dict['data_server']
        self.datahost = C[self.dataserv].host
        self.dataport = C[self.dataserv].port


        # stores the plateid
        self.plateid = '4534' # have one here for testing, else put it to ''
        
        
    async def get_alignment(self, plateid, motor, data):
        self.aligning = True

        # Don't want to copy the complete config, which is also unnecessary
        # these are the params the Visulalizer needs
        self.plateid = plateid
        if motor in C:
            self.motorhost = C[motor].host
            self.motorport = C[motor].port
            self.motorserv = motor
        else:
            print(f'Alignment Error. {motor} server not found.')
            return []

        if data in C:
            self.datahost = C[data].host
            self.dataport = C[data].port
            self.dataserv = data
        else:
            print(f'Alignment Error. {data} server not found.')
            return []

#        if visualizer in C:
#            self.vishost = C[visualizer].host 
#            self.visport = C[visualizer].port
#            self.visserv= visualizer
#        else:
#            print(f'Alignment Error. {visualizer} server not found.')
#            return []

        print(f'Plate Aligner web interface: http://{self.vishost}:{self.visport}/{self.visserv}')
        
        # now wait until bokeh server will set aligning to False via API call
        while self.aligning:
            await asyncio.sleep(1)            
        # should not be needed?
        self.aligning = False
            
        return {
            "Transfermatrix": self.newTransfermatrix,
            "err_code": self.errorcode,
            "plateid": self.plateid,
            "motor_server": self.motorserv,
            "data_server": self.dataserv
        }
    

    def is_aligning(self):
        return self.aligning


    def get_PM(self):
        response = requests.post(f"http://{self.datahost}:{self.dataport}/{self.dataserv}/get_platemap_plateid",
                        params={'plateid':self.plateid}).json()
        return response


    def get_position(self):
        response = requests.post(f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/query_positions",
                        params={}).json()
        return response


    def move(self, x_mm, axis, speed, mode):
        response = requests.post(f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/move",
                        params={'x_mm':x_mm,'axis':axis,'speed':speed,'mode':mode}).json()
        return response

    def ismoving(self, axis):
        response = requests.post(f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/query_moving",
                        params={'axis':axis}).json()
        return response

################## END Helper functions #######################################

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


app = FastAPI(title="Instrument alignment server",
    description="",
    version="1.0")


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"
    

class return_status(BaseModel):
    measurement_type: str
    parameters: dict
    status: dict


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


# only for alignment bokeh server
@app.post(f"/{servKey}/private/align_get_position")
async def private_align_get_position():
    """Return the current motor position"""
    # gets position of all axis, but use only axis defined in aligner server params
    # can also easily be 3d axis (but not implemented yet so only 2d for now)
    await stat.set_run()
    retc = return_class(
        measurement_type="alignment_command",
        parameters={},
        data=align.get_position(),
    )
    await stat.set_idle()
    return retc


# only for alignment bokeh server
@app.post(f"/{servKey}/private/align_move")
async def private_align_move(
    x_mm: str,
    axis: str,
    speed: int = None,
    mode: move_modes = "relative"
):
    stopping = False
    await stat.set_run()
    retc = return_class(
        measurement_type="alignment_command",
        parameters={
            "command": "move",
#            "motor":"def"},
            "x_mm": x_mm,
            "axis": axis,
            "speed": speed,
            "mode": mode,
            "stopping": stopping,
        },
        data=align.move(x_mm, axis, speed, mode),
    )
    await stat.set_idle()
    return retc


# only for alignment bokeh server
@app.post(f"/{servKey}/private/align_get_PM")
async def private_align_get_PM():
    """Returns the PM for the alignment Visualizer"""
    await stat.set_run()
    retc = return_class(
        measurement_type="alignment_command",
        parameters={"command": "get_PM",
                    "plateid": align.plateid,
                    },
        data=align.get_PM(),
    )
    await stat.set_idle()
    return retc


# only for alignment bokeh server
@app.post(f"/{servKey}/private/ismoving")
async def private_align_ismoving(axis: str):
    """check if motor is moving"""
    await stat.set_run()
    retc = return_class(
        measurement_type="alignment_command",
        parameters={"command": "align_ismoving",
                    "axis": axis
                    },
        data=align.ismoving(axis),
    )
    await stat.set_idle()
    return retc


# only for alignment bokeh server
@app.post(f"/{servKey}/private/send_alignment")
async def private_align_send_alignment(Transfermatrix: str, oldTransfermatrix: str, errorcode: str):
    """the bokeh server will send its Transfermatrix back with this"""
    await stat.set_run()

    retc = return_class(
        measurement_type="alignment_command",
        parameters={
            "command": "private_align_send_alignment",
        },
        data= {'err_code':errorcode,
               'Transfermatrix':Transfermatrix,
               'init_Transfermatrix':oldTransfermatrix
               },
    )
    # saving params from bokehserver so we can send them back
    align.newTransfermatrix = Transfermatrix
    align.errorcode = errorcode
    # signal to other function that we are done
    align.aligning = False
    print("received new alignment")
    await stat.set_idle()
    return retc # should not need that but we simply send the same data back to signal success


@app.on_event("startup")
def startup_event():
    global align
    align = aligner(S.params, C)
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


# TODO: alignment FastAPI and bokeh server are linked
# should motor server and data server be parameters?
# TODO: add mode to get Transfermatrix from Database?
@app.post(f"/{servKey}/get_alignment")
async def get_alignment(plateid: str,
                        motor: str="motor",#align.config_dict['motor_server'], # default motor server in config 
#                        visualizer: str=align.config_dict['vis_server'], # default visualizer in config
                        data: str="data",#align.config_dict['data_server'] # default data server in config
                        ):
    """Starts alignment process and returns TransferMatrix"""
    print('Getting alignment for:', plateid)
    
    await stat.set_run()
    retc = return_class(
        measurement_type="alignment_command",
        parameters={"command": "get_alignment",
                    "plateid": plateid,
                    "motor": motor,
                    "data": data,
#                    "visualizer":visualizer
                    },
        data={"TransferMatrix":await align.get_alignment(plateid, motor, data)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/align_status")
async def align_status():
    """Return status of current alignment"""
    # True: alignment is running, False: no alignment running
    await stat.set_run()
    retc = return_class(
        measurement_type="alignment_command",
        parameters={"command": "get_PM",
                    },
        data={"aligning": align.is_aligning()},
    )
    await stat.set_idle()
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
    return ""


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
