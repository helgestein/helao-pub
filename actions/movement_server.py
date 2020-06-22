#from config import mischbares_small
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
    
@app.get("/movement/movehome")
def move_to_home():
    return_fnc = m.move_to_home()
    data = requests.get("{}/movement/homing".format(mecademic_url), params={"homing": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'movetohome'},
                        data = {'data': data})
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

@app.get("/movement/aligningsample")
def align_sample():
    return_fnc = m.align_sample()
    data = requests.get("{}/movement/samplealignment".format(mecademic_url), params={"sample_alignment": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'samplealignment'},
                        data = {'data': data})
    return retc

@app.get("/movement/aligningres")
def align_reservoir():
    m.align_reservoir()
    data = requests.get("{}/movement/resalignment".format(mecademic_url), params={"reservoir_alignment": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'resalignment'},
                        data = {'data': data})
    return retc


@app.get("/movement/aligningwaste")
def align_waste():
    m.align_waste()
    data = requests.get("{}/movement/wastealignment".format(mecademic_url), params={"waste_alignment": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'wastealignment'},
                        data = {'data': data})
    return retc


@app.get("/movement/alignment")
def alignment():
    m.alignment()
    data = requests.get("{}/movement/alignment".format(mecademic_url), params={"alignment": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'alignment'},
                        data = {'data': data})
    return retc

@app.get("/movement/movetosample")
def mv2sample(x: float, y: float):
    m.mv2sample(x, y)
    data = requests.get("{}/movement/movesamp".format(mecademic_url), params={"movetosample": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'move2sample'},
                        data = {'data': data})
    return retc


@app.get("/movement/movetores")
def mv2res(x: float, y: float):
    m.mv2reservoir(x, y)
    data = requests.get("{}/movement/moveres".format(mecademic_url), params={"movetores": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'move2res'},
                        data = {'data': data})
    return retc



@app.get("/movement/moveup")
def moveup(z: float=50):
    m.moveup(z)
    data = requests.get("{}/movement/moveupward".format(mecademic_url), params={"z": z}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'moveup'},
                        data = {'data': data})
    return retc

@app.get("/movement/removedrop")
def removedrop(y: float=20):
    m.removedrop(y)
    data = requests.get("{}/movement/removal".format(mecademic_url), params={"y": y}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'dropremoved'},
                        data = {'data': data})
    return retc


@app.get("/movement/movetowaste")
def move2waste(x: float, y: float):
    m.mv2waste(x, y)
    data = requests.get("{}/movement/mv2waste".format(mecademic_url), params={"movetowaste": "done"}).json()

    retc = return_class(measurement_type='movement_command',
                        parameters= {'command':'move2waste'},
                        data = {'data': data})
    return retc

if __name__ == "__main__":
    m = Movements()
    mecademic_url = "http://{}:{}".format("127.0.0.1", "13370")
    uvicorn.run(app, host="127.0.0.1", port=13371)
    print("instantiated mecademic")