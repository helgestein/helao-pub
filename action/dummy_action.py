#implement a really stupid action
import sys
import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="arcoptix ftir server V1", 
    description="This is a fancy arcoptix ftir spectrometer action server", 
    version="1.0")


class return_class(BaseModel):
    parameters: dict = None
    data: str = None

@app.get("/dummy/lmao")
def lmao(t:float):
    time.sleep(t)
    print(f"waiting for {t} seconds")
    retc = return_class(parameters={'t':t,'units':{'t':'s'}},data="look at htis nice data")
    return retc

if __name__ == "__main__":
    uvicorn.run(app,host=config['servers'][serverkey]['host'],port=config['servers'][serverkey]['port'])
    print("instantiated an idiotic action")
