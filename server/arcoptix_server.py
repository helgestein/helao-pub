import sys
import uvicorn
from fastapi import FastAPI,WebSocket
from pydantic import BaseModel
import asyncio
import json
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(helao_root)
from arcoptix_driver import arcoptix
from util import compress_spectrum
config = import_module(sys.argv[1]).config

app = FastAPI(title="ocean driver", 
            description= " this is a fancy arctoptix ftir spectrometer driver server",
            version= "1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None


@app.on_event("startup")
def startup_event():
    global a,q
    a = arcoptix(config['arcoptix'])
    q = asyncio.Queue()

@app.get("/arcoptix/spectrum")
async def getSpectrum(filename:str):
    data = a.getSpectrum(filename)
    await q.put(compress_spectrum(data,10,["wavelengths","intensities"]))
    retc = return_class(parameters = {"filename" : filename},
                        data = data)
    return retc

@app.get("/arcoptix/read")
def readSpectrum(av:int=1):
    a.readSpectrum(av)
    retc = return_class(parameters = {"av" : av},data = None)
    return retc

@app.get("/arcoptix/readTime")
def readSpectrumTime(time:float):
    a.readSpectrumTime(time)
    retc = return_class(parameters = {"time" : time,'units':'??'},data = None)
    return retc


@app.get("/arcoptix/loadFile")
def loadFile(filename:str):
    data = a.loadFile(filename)
    retc = return_class(parameters = {"filename" : filename},data = data)
    return retc


@app.websocket("/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await q.get()
        await websocket.send_text(json.dumps(data))


if __name__ == "__main__":
    uvicorn.run(app, host=config['servers']['arcoptixServer']['host'], port=config['servers']['arcoptixServer']['port'])
    print("instantiated ftir spectrometer")