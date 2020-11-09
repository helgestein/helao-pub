import sys
import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import json
sys.path.append(r"..\config")
from mischbares_small import config
import random
import asyncio

app = FastAPI(title="ocean driver", 
            description= " this is a fake ocean optics raman spectrometer driver server",
            version= "1.0")


class ocean:
    def __init__(self):
        self.q = asyncio.Queue()


    async def readSpectrum(self):
        data = {"wavelengths":[i for i in range(100)],"intensities":[random.randint(0,10) for i in range(100)]}
        await self.q.put(json.dumps(data))
        return data


@app.on_event("startup")
def startup_event():
    global o
    o = ocean()


@app.post("/ocean/readSpectrum")
async def readSpectrum():
    return await o.readSpectrum()

@app.websocket("/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await o.q.get()
        await websocket.send_text(data)


if __name__ == "__main__":
    uvicorn.run(app, host=config['servers']['oceanServer']['host'], port=config['servers']['oceanServer']['port'])
    print("instantiated raman spectrometer")