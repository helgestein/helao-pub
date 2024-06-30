from typing import List
import json
from pydantic import BaseModel
from fastapi import FastAPI, Query, WebSocket
import uvicorn
import sys
import os
import time
import re
import queue
import asyncio
import websockets
from importlib import import_module
from contextlib import asynccontextmanager
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
from palmsens_driver import PalmsensDevice
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    global p
    p = PalmsensDevice()
    yield
    await p.disconnect()

app = FastAPI(lifespan=app_lifespan, title="PalmSens v.1.0",
              description="This is a very fancy PalmSens Driver server",
              version="1.0")

@app.get("/palmsensDriver/measure")
def measure(method:str, parameters:str, filename:str):
    params = eval(parameters.replace('true', 'True').replace('false', 'False'))
    print(params)
    #params = json.loads(parameters)
    ret = p.measure(method=method, parameters=params, filename=filename)
    retc = return_class(parameters={'procedure': 'measure',
                                    'method': method,
                                    'parameters': params,
                                    'filename': filename},
                        data=ret)
    return retc

@app.get("/palmsensDriver/retrieveData")
def retrieveData(filename:str):
    ret = p.retrieveData(filename=filename)
    retc = return_class(parameters={'procedure': 'retrieveData',
                                    'filename': filename},
                        data=ret)
    return retc

@app.websocket("/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            data = p.queue.get(block=False)
            data["timestamp"] = time.time()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.05)
        except queue.Empty:
            await asyncio.sleep(0.05)
            continue
        except websockets.exceptions.ConnectionClosedError:
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(0.05)


if __name__ == "__main__":
    uvicorn.run(app, host=config['servers'][serverkey]
                ['host'], port=config['servers'][serverkey]['port'])
