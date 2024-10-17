import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import time
import json
import os
from importlib import import_module

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="Hamilton Microlab 600 syringe pump action server V1",
    description="This is a very fancy pump action server",
    version="2.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/microlab/pumpL/")
def pumpSingleL(volume: int=0, times:int=1):
    #we usually had all volumes for the other pumps in microliters
    #so here we expect he input to be in microliters and convert it to nL

    volnl = volume*1000
    retl = []

    if volnl>0:
        In = 'prefIn'
        Out = 'prefOut'
    else:
        In = 'prefOut'
        Out = 'prefIn'
    
    for i in range(times):
        #first aspirate a negative volume through the preferred in port
        aspparam = dict(leftVol=abs(volnl),rightVol=0,
                        leftPort=config[serverkey]['left']['valve'][In],rightPort=0,
                        delayLeft=0,delayRigh=0)
        res = requests.get("{}/microlabDriver/pump".format(hamiltonurl),
                            params=aspparam).json()
        retl.append(res)
        #then eject through the preferred out port
        aspparam = dict(leftVol=-abs(volnl),rightVol=0,
                        leftPort=config[serverkey]['left']['valve'][Out],rightPort=0,
                        delayLeft=0,delayRigh=0)
        res = requests.get("{}/microlabDriver/pump".format(hamiltonurl),
                            params=aspparam).json()
        retl.append(res)

    retc = return_class(parameters= {'volumeL':volume,'times':times},
                        data = {i:retl[i] for i in range(len(retl))})
    return retc

@app.get("/microlab/pumpR/")
def pumpSingleR(volume: int=0, times:int=1):
    #we usually had all volumes for the other pumps in microliters
    #so here we expect he input to be in microliters and convert it to nL

    volnl = volume*1000
    retl = []

    if volnl>0:
        In = 'prefIn'
        Out = 'prefOut'
    else:
        In = 'prefOut'
        Out = 'prefIn'

    for i in range(times):
        #first aspirate a negative volume through the preferred in port
        aspparam = dict(leftVol=0,rightVol=abs(volnl),
                        leftPort=0,rightPort=config[serverkey]['right']['valve'][In],
                        delayLeft=0,delayRigh=0)
        res = requests.get("{}/microlabDriver/pump".format(hamiltonurl),
                            params=aspparam).json()
        retl.append(res)
        #then eject through the preferred out port
        aspparam = dict(leftVol=0,rightVol=-abs(volnl),
                        leftPort=0,rightPort=config[serverkey]['right']['valve'][Out],
                        delayLeft=0,delayRigh=0)
        res = requests.get("{}/microlabDriver/pump".format(hamiltonurl),
                            params=aspparam).json()
        retl.append(res)

    retc = return_class(parameters= {'volumeR':volume,'times':times},
                        data = {i:retl[i] for i in range(len(retl))})
    return retc

#TODO: implement a formulation aspiration
#this could be done by aspiration a volume left stepvise from different vials
#then rocking it back and forth between left and right syringe and then eject
#through the right syringe. The only thing we need in addition is a valve 

if __name__ == "__main__":
    #pumpurl = "http://{}:{}".format(config['servers']['pumpServer']['host'], config['servers']['pumpServer']['port'])
    #uvicorn.run(app, host=config['servers']['pumpingServer']['host'],
    #                 port=config['servers']['pumpingServer']['port'])
    hamiltonurl = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'],
                     port=config['servers'][serverkey]['port'])
