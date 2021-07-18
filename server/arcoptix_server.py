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
serverkey = sys.argv[2]

app = FastAPI(title="ocean driver", 
            description= " this is a fancy arctoptix ftir spectrometer driver server",
            version= "1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: dict = None


@app.on_event("startup")
def startup_event():
    global a,q
    a = arcoptix(config[serverkey])
    q = asyncio.Queue()


#416:2501
@app.get("/arcoptixDriver/spectrum")
async def getSpectrum(filename:str,time:bool=False,av:float=1,wlrange:str=None,wnrange:str=None,inrange:str=None):
    data = a.getSpectrum(filename,time=time,av=av,wlrange=wlrange,wnrange=wnrange,inrange=inrange)
    await q.put({'wavelengths':data['wavelengths'],'intensities':data['intensities']})
    retc = return_class(parameters = {"filename":filename,"time":time,"av":av,"wlrange":wlrange,"wnrange":wnrange,"inrange":inrange,"units":{"av":"s or #spectra"}},
                        data = data)
    return retc

@app.get("/arcoptixDriver/setGain")
def setGain(gain:int):
    data = a.setGain(gain)
    retc = return_class(parameters={"gain":gain},data=None)
    return retc

@app.get("/arcoptixDriver/saturation")
def getSaturation():
    data = a.getSaturation()
    retc = return_class(parameters=None,data={"saturation":data})
    return retc

@app.get("/arcoptixDriver/getGain")
def getGain():
    data = a.getGain()
    retc = return_class(parameters=None,data={"gain":data})
    return retc

@app.get("/arcoptixDriver/loadFile")
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
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    print("instantiated ftir spectrometer")