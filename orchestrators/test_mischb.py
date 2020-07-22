# In order to run the orchatrator which is at the highest level of Helao, all servers should be started. 
import requests
import sys
sys.path.append(r'../config')
sys.path.append(r'../action')
sys.path.append(r'../server')
import time
from mischbares_small import config
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import json
import uvicorn
from typing import List
from fastapi import FastAPI, Query
import json


#### writing the orchastrator server
app = FastAPI(title = "orchestrator", description = "A fancy complex server",version = 1.0)

### define the experiment list
exp_list = ["ashdkajshdkjahksjd"]

@app.get("/a/add")
async def addToQueue(liste: list):

    zahl = liste.pop(0)
    exp_list[1] = ["askdjakjdskh"]
    print('added {}'.format(zahl))
    print('len of liste is: {}'.format(len(liste)))

@app.get("/a/executeexperiment")
def popping(liste):
    #poplist


if __name__ == "__main__":

    liste = []


    uvicorn.run(app, host= '127.0.0.1', port=23236)

    while not liste == []:
        addToQueue(liste)
        
    print("orchestrator is instantiated. ")
    
