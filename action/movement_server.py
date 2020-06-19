from config import mischbares_small
import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
from movement_mecademic import Movements
import requests
import time

app = FastAPI(title="Mecademic action server V1", 
    description="This is a fancy mecademic action server", 
    version="1.0")


mecademic_url = "http://{}:{}".format(FASTAPI_HOST, MOTION_PORT)

class return_class(BaseModel):
    measurement_type: str = None
    parameters :dict = None
    data: dict = None

@app.get("/movement/matrix_rotation")
def matrix_rotation(theta: float, request: Request):
    return_fnc = m.matrix_rotation(theta)
    
    data = requests.get(
        "{}/movement/rotation".format(mecademic_url),
        params={"theta": theta}).json()
    
    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'getmatrixrotation', "rotation_value": return_fnc},
                        data = {'data': data}
                        )
    return retc
    

@app.get("/movement/jogging")
def jogging(joints: int):
    return_pose, return_joint = m.jogging(joints)

    data = requests.get("{}/movement/jogging".format(mecademic_url),
        params={"joints": joints}).json()

    retc = return_class(measurement_type='movement_command',
                    parameters= {'command':'jogging_joints', "poses": return_pose,"joints": return_joint},
                    data = {'data': data}
                    )
    return retc


    





if __name__ == "__main__":
    m = Movements()
    uvicorn.run(app, host="127.0.0.1", port=13371)
    print("instantiated mecademic")