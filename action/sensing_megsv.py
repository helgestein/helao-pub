#implement the action-server for force sensor
import sys
sys.path.append(r'../driver')
sys.path.append(r'../config')
sys.path.append(r'../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import json
import requests

app = FastAPI(title="Force sensor action server V1", 
    description="This is a fancy force sensor action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None



@app.get("/forceAction/read")
def read():
    #read a force measurement from the buffer. if there is no measurement in the buffer, it will wait for one to arrive.
    while True:
        data = requests.get("{}/force/read".format(url)).json()
        if data['data']['value'] != None:
            break
    retc = return_class(parameters=None, data=data)
    return retc



if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['megsvServer']['host'],config['servers']['megsvServer']['port'])
    uvicorn.run(app,host=config['servers']['sensingServer']['host'],port=config['servers']['sensingServer']['port'])
    print("instantiated force sensor action")
    