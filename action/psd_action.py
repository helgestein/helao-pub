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
import asyncio
from importlib import import_module

helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="Hamilton PSD/4 syringe pump action server V1",
    description="This is a very fancy pump action server",
    version="1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/psd/pumpSimple")
def pumpSimple(volume: float=0, valve: int=1, speed: int=10, times: int=1):
    #we usually had all volumes for the other pumps in microliters
    #so here we expect he input to be in microliters and convert to steps from 0 to 3000 for psd4
    steps = int(round(volume/config[serverkey]['volume']*3000))
    
    # converted to angles from 0 to 315 degrees 
    valve_angle = int((valve-1) * 45)

    if volume > 0:
        In = valve_angle
        Out = int((config[serverkey]['valve']['Out']-1) * 45)
    else:
        In = int((config[serverkey]['valve']['Out']-1) * 45)
        Out = valve_angle
        
    response = {}

    if speed != config[serverkey]['speed']:
        speed_param = {'speed': speed}
        response['speed'] = requests.get("{}/psdDriver/speed".format(psdurl),
                            params=speed_param).json()
        

    for i in range(times):
        #first aspirate a negative volume through the preferred in port
        valve_param = {'valve_angle': In}
        asp_param = {'step': abs(steps)}
        response[f'valveIn_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                            params=valve_param).json()
        time.sleep(0.2)
        response[f'pumpIn_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                            params=asp_param).json()
        time.sleep(0.2)
        #then eject through the preferred out port
        valve_param = {'valve_angle': Out}
        asp_param = {'step': 0}
        response[f'valveOut_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                            params=valve_param).json()
        time.sleep(0.2)
        response[f'pumpOut_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                            params=asp_param).json()
        time.sleep(0.2)

    retc = return_class(parameters= {'valve': valve,'volume (uL)': volume, 'speed': speed, 'times': times},
                        data = response)
    return retc


@app.get("/psd/pumpMix")
def pumpMix(V1: float=0, V2: float=0, V3: float=0, V4: float=0, V5: float=0, V6: float=0, mix_speed: int=20, mix: int=1, vial_speed: int=10, times: int=1, cell: bool=False):
    #we usually had all volumes for the other pumps in microliters
    #so here we expect he input to be in microliters and convert to steps from 0 to 3000 for psd4
    #the sum of all volumes should be less than the syringe volume
    V = abs(V1)+abs(V2)+abs(V3)+abs(V4)+abs(V5)+abs(V6)
    if V > config[serverkey]['volume']:
        return "Error: the sum of all volumes should be less than the syringe volume"
    else:
        s1 = int(round(V1/config[serverkey]['volume']*3000))
        s2 = int(round(V2/config[serverkey]['volume']*3000))
        s3 = int(round(V3/config[serverkey]['volume']*3000))
        s4 = int(round(V4/config[serverkey]['volume']*3000))
        s5 = int(round(V5/config[serverkey]['volume']*3000))
        s6 = int(round(V6/config[serverkey]['volume']*3000))
        response = {}

    if mix_speed != config[serverkey]['speed']:
        speed_param = {'speed': mix_speed}
        response['speed'] = requests.get("{}/psdDriver/speed".format(psdurl),
                            params=speed_param).json()

    for i in range(times):
        summ = 0
        for j, s in enumerate([s1, s2, s3, s4, s5, s6], start=1):
            if s != 0:
                #first aspirate all volumes through the preferred in port
                valve_param = {'valve_angle': int((config[serverkey]['valve']['S{}'.format(j)] - 1) * 45)}
                summ += s
                asp_param = {'step': abs(summ)}
                response[f'valveIn_{j}_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                            params=valve_param).json()
                response[f'pumpIn_{j}_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                            params=asp_param).json()
                time.sleep(0.2)
        if mix != 0:
            if vial_speed != config[serverkey]['speed']:
                speed_param = {'speed': vial_speed}
                response['speed_mix'] = requests.get("{}/psdDriver/speed".format(psdurl),
                                    params=speed_param).json()
            for k in range(abs(mix)):        
                #then eject through the preferred out port to the vial
                valve_param = {'valve_angle': int((config[serverkey]['valve']['Mix']-1)*45)}
                asp_param = {'step': 0}
                response[f'valveVialIn_{k}_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                                    params=valve_param).json()
                response[f'pumpVialIn_{k}_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                    params=asp_param).json()
                time.sleep(0.2)
                #then aspirate through the preferred out port from the vial
                valve_param = {'valve_angle': int((config[serverkey]['valve']['Mix']-1)*45)}
                sum = abs(s1)+abs(s2)+abs(s3)+abs(s4)+abs(s5)+abs(s6)
                asp_param = {'step': abs(sum)}
                response[f'valveVialOut_{k}_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                                    params=valve_param).json()
                response[f'pumpVialOut_{k}_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                    params=asp_param).json()
                time.sleep(0.2)
        # decide whether to eject to the cell or to the vial
        if mix_speed != config[serverkey]['speed']:
            speed_param = {'speed': mix_speed}
            response['speed_back'] = requests.get("{}/psdDriver/speed".format(psdurl),
                                params=speed_param).json()
        if cell == False:
            #eject the whole volume back to the vial
            valve_param = {'valve_angle': int((config[serverkey]['valve']['Mix']-1)*45)}
            asp_param = {'step': 0}
            response[f'valveVialBack_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                                params=valve_param).json()
            response[f'pumpVialBack_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                params=asp_param).json()
            time.sleep(0.2)
        else:
            #then eject the whole volume through the preferred out port to the cell
            valve_param = {'valve_angle': int((config[serverkey]['valve']['Out']-1)*45)}
            asp_param = {'step': 0}
            response[f'valveOut_{i}'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                                params=valve_param).json()
            response[f'pumpOut_{i}'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                params=asp_param).json()
            time.sleep(0.2)

    retc = return_class(
    parameters={
        'V1': V1, 'V2': V2, 'V3': V3, 'V4': V4, 'V5': V5, 'V6': V6,
        'mix_speed': mix_speed, 'mix': mix, 'vial_speed': vial_speed,
        'times': times, 'cell': cell
    },
    data=response)
    return retc

@app.get("/psd/pumpVial")
def pumpVial(volume: float=0, speed: int=10, times: int=1):
    #we usually had all volumes for the other pumps in microliters
    #so here we expect he input to be in microliters and convert to steps from 0 to 3000 for psd4
    #here we are pumping only between the vial and the cell
    response = {}

    steps = int(round(volume/config[serverkey]['volume']*3000))

    if speed != config[serverkey]['speed']:
        speed_param = {'speed': speed}
        response['speed'] = requests.get("{}/psdDriver/speed".format(psdurl),
                            params=speed_param).json()

    if volume > 0:
        #if volume is positive, then pump from vial to syringe and then to cell
        valve_param = {'valve_angle': int((config[serverkey]['valve']['Mix']-1)*45)}
        response['valveIn'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                                    params=valve_param).json()
        asp_param = {'step': abs(steps)}
        response['pumpIn'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                    params=asp_param).json()
        time.sleep(0.2)
        valve_param = {'valve_angle': int((config[serverkey]['valve']['Out']-1)*45)}
        response['valveOut'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),	
                                    params=valve_param).json()
        asp_param = {'step': 0}
        response['pumpOut'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                    params=asp_param).json()
        time.sleep(0.2)
    else:
        #if volume is negative, then pump from cell to syringe and then to vial
        valve_param = {'valve_angle': int((config[serverkey]['valve']['Out']-1)*45)}
        response['valveOut'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),	
                                    params=valve_param).json()
        asp_param = {'step': abs(steps)}
        response['pumpOut'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                    params=asp_param).json()
        time.sleep(0.2)
        valve_param = {'valve_angle': int((config[serverkey]['valve']['Mix']-1)*45)}
        response['valveIn'] = requests.get("{}/psdDriver/valve_angle".format(psdurl),
                                    params=valve_param).json()
        asp_param = {'step': 0}
        response['pumpIn'] = requests.get("{}/psdDriver/pump".format(psdurl),
                                    params=asp_param).json()
        time.sleep(0.2)

    retc = return_class(parameters= {'volume': volume, 'speed': speed, 'times': times},
                        data = response)
    return retc

@app.get("/psd/pumpRead")
def read():
    response = {}
    response = requests.get("{}/psdDriver/read".format(psdurl),
                                params={}).json()
    retc = return_class(parameters={},
                        data = response)
    return retc

if __name__ == "__main__":
    psdurl = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'],
                     port=config['servers'][serverkey]['port'])