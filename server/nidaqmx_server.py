# NIdaqmx server
# https://nidaqmx-python.readthedocs.io/en/latest/task.html
# http://127.0.0.1:8006/docs#/default


import os
import sys

from importlib import import_module
import json
import uvicorn

from fastapi import FastAPI, WebSocket
from fastapi.openapi.utils import get_flat_params
from pydantic import BaseModel
from munch import munchify

#import requests
#import asyncio
#import aiohttp
#from enum import Enum
#import numpy as np

import nidaqmx


helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(os.path.join(helao_root, 'core'))
from classes import StatusHandler



################## Helper functions ##########################################
# this could also move into a separate driver, but should not be necessary
# as all of this can also be in the FastAPI functions itself
class cNIMAX:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        print('NIMAX config:')
        print(self.config_dict)
        print('init NIMAX')


    async def set_activate_cells(self, cells):
        cell_list = await self.sep_cellsstr(cells)
        print('activating cells:', cell_list)


    async def get_cell_current(self, cells):
        cell_list = await self.sep_cellsstr(cells)
        print('Getting cell current:', cell_list)
         

    async def get_cell_diffV(self, cells):
        cell_list = await self.sep_cellsstr(cells)
        print('Getting cell diffV:', cell_list)


    # this is a demo/debug task. Need to go to action library later
    async def run_task1(self, cells):
        cell_list = await self.sep_cellsstr(cells)
        print('runnig task 1 on:', cell_list)


    async def sep_cellsstr(self, cells):  
        sepvals = [',','\t',';','::',':']
        new_cells = None
        for sep in sepvals:
            if not (cells.find(sep) == -1):
                    new_cells = cells.split(sep)
                    break    

        # single axis
        if new_cells == None:
            new_cells = cells

        return new_cells


################## END Helper functions #######################################

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"{confPrefix}").config
C = munchify(config)["servers"]
S = C[servKey]


app = FastAPI(title="NIdaqmx server",
    description="",
    version="1.0")


class return_status(BaseModel):
    measurement_type: str
    parameters: dict
    status: dict


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None





@app.post(f"/{servKey}/set_active_cells")
async def set_active_cells(cells: str):
    """Activates a cell, separate multiple cells by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "set_active_cells",
                    "parameters": {
                                        "cells": cells,
                                    },
                    },
        data=await NIMAX.set_activate_cells(cells),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_cell_current")
async def get_cell_current(cells: str):
    """gets cell current, separate multiple cells by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "get_cell_current",
                    "parameters": {
                                        "cells": cells,
                                    },
                    },
        data=await NIMAX.get_cell_current(cells),
    )
    await stat.set_idle()
    return retc


@app.post(f"/{servKey}/get_cell_diffV")
async def get_cell_diffV(cells: str):
    """gets cell differential voltage, separate multiple cells by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "get_cell_diffV",
                    "parameters": {
                                        "cells": cells,
                                    },
                    },
        data=await NIMAX.get_cell_diffV(cells),
    )
    await stat.set_idle()
    return retc


# TODO: put this later in a action libary (only for test here for now)
@app.post(f"/{servKey}/task_Channels_SampClk")
async def task_Channels_SampClk(cells: str):
    """Action TASK1, separate multiple cells by ,"""
    await stat.set_run()
    retc = return_class(
        measurement_type="NImax_command",
        parameters={
                    "command": "run_task1",
                    "parameters": {
                                        "cells": cells,
                                    },
                    },
        data=await NIMAX.run_task1(cells),
    )
    await stat.set_idle()
    return retc


@app.on_event("startup")
def startup_event():
    global NIMAX
    NIMAX = cNIMAX(S.params)
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