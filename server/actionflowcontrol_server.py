import os
import sys
import json
from importlib import import_module
#from asyncio import Queue
#from time import strftime
import asyncio


import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from munch import munchify

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))

from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsConnectionManager
from classes import sample_class
from classes import getuid
from classes import action_runparams
from classes import Action_params

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


# check if 'simulate' settings is present
if not 'simulate' in S:
    # default if no simulate is defined
    print('"simulate" not defined, switching to Gamry Simulator.')
    S['simulate']= False


if S.simulate:
    print('Gamry simulator loaded.')
    from gamry_simulate import gamry
else:
    from gamry_driver import gamry
    from gamry_driver import Gamry_Irange


app = FastAPI(title=servKey,
              description="ORCH ACTIONs", version=1.0)


@app.on_event("startup")
def startup_event():
    global stat
    stat = StatusHandler()
    # global wsdata
    # wsdata = wsConnectionManager()
    global wsstatus
    wsstatus = wsConnectionManager()
    
    
    
# @app.websocket(f"/{servKey}/ws_data")
# async def websocket_data(websocket: WebSocket):
#     await wsdata.send(websocket, poti.wsdataq, 'Gamry_data')


# as the technique calls will only start the measurment but won't return the final results
@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.send(websocket, stat.q, 'Gamry_status')
  
        
@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return stat.dict


@app.post(f"/{servKey}/action_wait")
async def action_wait(waittime: float = 0.0):
    """Sleep action"""    
    uid = getuid(servKey)
    await stat.set_run(uid, "action_wait")
    print(' ... wait action:', waittime)
    await asyncio.sleep(waittime)
    print(' ... wait action done')
    await stat.set_idle(uid, "action_wait")
    return {}


@app.post(f"/{servKey}/action_NOP")
async def action_wait(waittime: float = 0.0):
    """NOP action"""    
    uid = getuid(servKey)
    await stat.set_run(uid, "action_wait")
    await stat.set_idle(uid, "action_wait")
    return {}


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

@app.on_event("shutdown")
def shutdown_event():
    # this gets called when the server is shut down or reloaded to ensure a clean
    # disconnect ... just restart or terminate the server
    return {"shutdown"}


if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)    
    
    