import sys
sys.path.append(r"..\config")
sys.path.append(r"..\driver")
from ocean_driver import ocean
from mischbares_small import config
import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import json
import asyncio

app = FastAPI(title="ocean driver", 
            description= " this is a fancy ocean optics raman spectrometer driver server",
            version= "1.0")

class return_class(BaseModel):
    measurement_type: str = None
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
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "find_device"},
                        data = {"device" : str(device)})
    return retc

@app.get("/ocean/connect")
def open():
    o.open()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "open"},
                        data = {"status" : "activated"})
    return retc

@app.get("/ocean/readSpectrum")
async def readSpectrum(filename:str):
    data = o.readSpectrum(filename)
    await q.put(json.dumps(data))
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"filename" : filename},
                        data = data)
    return retc

@app.get("/ocean/loadFile")
def loadFile(filename:str):
    data = o.loadFile(filename)
    retc = return_class(measurement_type = "ocean_raman_command",
                    parameters = {"filename" : filename},
                    data = {"data" : data})
    return retc

@app.on_event("shutdown")
def close(self):
    o.close()
    retc = return_class(measurement_type = "ocean_raman_command",
                        parameters = {"command" : "close"},
                        data = {"status" : "deactivated"})
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