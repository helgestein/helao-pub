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

app = FastAPI(title="Force action server V1", 
    description="This is a fancy force action server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters :dict = None
    data: dict = None



@app.get("/forceAction/read")
def read():
    while True:
        
        data = requests.get("{}/force/read".format(url)).json()
        if data['data']['value'] != None:
            break
    retc = return_class(measurement_type='movement_command', 
                            parameters= {'command':'read_data'}, 
                            data = {'data': data})
    return retc






if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['forceServer']['host'], config['servers']['forceServer']['port'])
    
    uvicorn.run(app, host=config['servers']['forcActioneServer']['host'], port=config['servers']['forcActioneServer']['port'])
    print("instantiated force action")
    