import sys
import os
import time
import re
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
config = import_module(sys.argv[1]).config
from autolab_driver import Autolab
import uvicorn
from fastapi import FastAPI, Query, WebSocket
from pydantic import BaseModel
import json
from typing import List



app = FastAPI(title="Autolab V2",
    description="This is a very fancy autolab server",
    version="2.0",)

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

class Item(BaseModel):
    name: str

class ItemList(BaseModel):
    items: List[Item]

@app.on_event("startup")
def startup_event():
    global a
    a = Autolab(config['autolab'])


@app.get("/autolab/ismeasuring")
def ismeasuring():
    ret = a.ismeasuring()
    retc = return_class(parameters= None,data = {'ismeasuring':ret})
    return retc

@app.get("/autolab/potential")
def potential():
    ret = a.potential()
    retc = return_class(parameters= None,data = {'potential':ret,'units':'V'})
    return retc

@app.get("/autolab/current")
def current():
    ret = a.current()
    retc = return_class(parameters= None,data = {'current':ret,'units':'A'})
    return retc

@app.get("/autolab/setcurrentrange")
def setCurrentRange(crange: str):
    a.setCurrentRange(crange)
    res = [re.findall(r'(\d+)(\w+)', crange)[0]]
    retc = return_class(parameters= {'parameters':crange,'units': res[0][1]},data = None)
    return retc

@app.get("/autolab/setstability")
def setStability(stability:str):
    a.setStability(stability)
    retc = return_class(parameters={'stability':stability},data = None)
    return retc

@app.get("/autolab/appliedpotential")
def appliedPotential():
    ret = a.appliedPotential()
    retc = return_class(parameters= None,data = {'appliedpotential':ret,'units':'V'})
    return retc

@app.websocket("/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await a.q.get()
        print('data: '+str(data))
        data = {k: [v] for k, v in zip(["t_s", "freq", "Ewe_V", "Ach_V", "Z_real", "Z_imag", "phase", "modulus", "I_A"], data)}
        await websocket.send_text(json.dumps(time.time()))
        await websocket.send_text(json.dumps(data))



@app.get("/autolab/abort")
def abort():
    a.abort()
    retc = return_class(parameters= None,data= None)
    return retc

@app.get("/autolab/cellonoff")
def CellOnOff(onoff:str):
    a.CellOnOff(onoff)
    retc = return_class(parameters= {'onoff':onoff},data = None)
    return retc

@app.get("/autolab/measure")
async def performMeasurement(procedure: str,setpointjson: str ,plot:str,onoffafter:str,safepath:str,filename:str, parseinstructions:str):
    setpoints = eval(setpointjson)
    #setpoint_keys = list(setpoints.keys())
    #setpoint_values = [setpoints[k] for k in setpoint_keys]


    parseinstruction = [parseinstructions]
    data = await a.performMeasurement(procedure,setpoints,plot,onoffafter,safepath,filename, parseinstruction)
    retc = return_class(measurement_type='potentiostat_autolab',
                    parameters= {'command':'measure',
                                'parameters':dict(procedure=procedure,setpointjson= setpointjson,
                                                  plot=plot,onoffafter=onoffafter,safepath=safepath,filename=filename, parseinstruction= parseinstruction)},
                    data = data)
    return retc


@app.get("/autolab/retrieve")
def retrieve(safepath:str,filename:str):
    conf = dict(safepath=safepath,filename=filename)
    path = os.path.join(conf['safepath'],conf['filename'])
    with open(path.replace('.nox', '_data.json'), 'r') as f:
        ret = json.load(f)
    retc = return_class(parameters= {'safepath':safepath,'filename':filename},
                        data = {'appliedpotential':ret})
    return retc

@app.on_event("shutdown")
def disconnect():
    a.disconnect()

if __name__ == "__main__":
    uvicorn.run(app, host=config['servers']['autolab']['host'], port=config['servers']['autolab']['port'])
