import sys
import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import json
import asyncio
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
from ocean_driver import ocean
config = import_module(sys.argv[1]).config


app = FastAPI(title="ocean driver", 
            description= " this is a fancy ocean optics raman spectrometer driver server",
            version= "1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.on_event("startup")
def startup_event():
    global o,q
    o = ocean()
    q = asyncio.Queue()

@app.get("/ocean/find")
def findDevice():
    device = o.findDevice()
    retc = return_class(parameters = None,data = {"device" : str(device)})
    return retc

@app.get("/ocean/connect")
def open():
    o.open()
    retc = return_class(parameters = None,data = None)
    return retc

@app.get("/ocean/readSpectrum")
async def readSpectrum(t:int,filename:str):
    data = o.readSpectrum(t,filename)
    await q.put(data)
    retc = return_class(parameters = {"filename" : filename, "t" : t,'units':{'t':'µs'}},data = data)
    return retc

@app.get("/ocean/loadFile")
def loadFile(filename:str):
    data = o.loadFile(filename)
    retc = return_class(parameters = {"filename" : filename},data = data)
    return retc

@app.on_event("shutdown")
def close(self):
    o.close()
    retc = return_class(parameters = None,data = None)
    return retc


@app.websocket("/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await q.get()
        await websocket.send_text(json.dumps(data))


if __name__ == "__main__":
    uvicorn.run(app, host=config['servers']['oceanServer']['host'], port=config['servers']['oceanServer']['port'])
    print("instantiated raman spectrometer")