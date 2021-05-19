# data management server for HTE

import os
import sys

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
from classes import StatusHandler
from classes import return_status
from classes import return_class
from classes import wsConnectionManager

import asyncio
import time




confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]



# check if 'mode' setting is present
if not 'mode' in S:
    print('"mode" not defined, switching to lagacy mode.')
    S['mode']= "lagacy"


if S.mode == "legacy":
    print("Legacy data managament mode")
    from HTEdata_legacy import HTEdata
elif S.mode == "modelyst":
    print("Modelyst data managament mode")
#    from HTEdata_modelyst import HTEdata
else:
    print("Unknown data mode")
#    from HTEdata_dummy import HTEdata


app = FastAPI(title="HTE data management server",
    description="",
    version="1.0")


@app.on_event("startup")
def startup_event():
    global dataserv
    dataserv = HTEdata(S.params)
    global stat
    stat = StatusHandler()

    global wsdata
    wsdata = wsConnectionManager()
    global wsstatus
    wsstatus = wsConnectionManager()


@app.websocket(f"/{servKey}/ws_status")
async def websocket_status(websocket: WebSocket):
    await wsstatus.send(websocket, stat.q, 'data_status')


@app.post(f"/{servKey}/get_status")
def status_wrapper():
    return stat.dict


# broadcast platemap and id etc
@app.websocket(f"/{servKey}/ws_data")
async def websocket_data(websocket: WebSocket):
    await wsdata.send(websocket, dataserv.qdata, 'data_data')


@app.post(f"/{servKey}/get_elements_plateid")
async def get_elements_plateid(plateid: str, action_params = ''):
    """Gets the elements from the screening print in the info file"""
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "get_elements_plateid"},
        data={"elements": dataserv.get_elements_plateidstr(plateid)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_platemap_plateid")
async def get_platemap_plateid(plateid: str, action_params = ''):
    """gets platemap"""
    await stat.set_run()
    retval = dataserv.get_platemap_plateidstr(plateid)
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "get_platemap_plateid"},
        data={"map": retval},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_platexycalibration")
async def get_platexycalibration(plateid, action_params = ''):
    """gets saved plate alignment matrix"""
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "get_platexycalibration"},
        data={"matrix": None}, # need to read it from K or database
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/save_platexycalibration")
async def save_platexycalibration(plateid, action_params = ''):
    """saves alignment matrix"""
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "save_platexycalibration"},
        data={"matrix": None}, # get it from motion server
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/check_plateid")
async def check_plateid(plateid, action_params = ''):
    """checks that the plate_id (info file) exists"""
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "check_plateid"},
        data={"bool": dataserv.check_plateidstr(plateid)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/check_printrecord_plateid")
async def check_printrecord_plateid(plateid: str, action_params = ''):
    """checks that a print record exist in the info file"""
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "check_printrecord_plateid"},
        data={"bool": dataserv.check_printrecord_plateidstr(plateid)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/check_annealrecord_plateid")
async def check_annealrecord_plateid(plateid: str, action_params = ''):
    """checks that a anneal record exist in the info file"""
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "check_annealrecord_plateid"},
        data={"bool": dataserv.check_annealrecord_plateidstr(plateid)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_info_plateid")
async def get_info_plateid(plateid: str, action_params = ''):
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "get_info_plateid"},
        data={"info": dataserv.get_info_plateidstr(plateid)},
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_rcp_plateid")
async def get_rcp_plateid(plateid: str, action_params = ''):
    await stat.set_run()
    retc = return_class(
        measurement_type="data_command",
        parameters={"command": "get_rcp_plateid"},
        data={"info": dataserv.get_rcp_plateidstr(plateid)},
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


@app.post("/shutdown")
def post_shutdown():
    shutdown_event()


@app.on_event("shutdown")
def shutdown_event():
    return ""

    
if __name__ == "__main__":
    uvicorn.run(app, host=S.host, port=S.port)
