#(c) Prof.-jun. Dr.-Ing. Helge Sören Stein 2020
#this is a program for the CAT Engineering MDPS Multichannel Pump
#besides this this is also a reference implementation for a HELAO driver

import serial
import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Pump server V1",
    description="This is a very fancy pump server",
    version="1.0",)

class return_class(BaseModel):
    measurement_type: str = None
    parameters: dict = None
    data: dict = None

@app.get("/pump/isBlocked")
def isBlocked(pump: int):
    ret = p.isBlocked(pump)
    retc = return_class(*ret)
    return retc

@app.get("/pump/setBlock")
def setBlock(pump:int, time_block:float):
    #this sets a block
    ret = p.setBlock(pump,time_block)
    retc = return_class(ret)
    return retc

@app.get("/pump/dispenseVolume")
def dispenseVolume(pump:int ,volume:int ,speed:int ,direction:int=1,read=False):
    #pump is an index 0-13 incicating the pump channel
    #volume is the volume in µL
    #speed is a variable 0-1 going from 0µl/min to 4000µL/min

    ser.write(bytes('{},PON,1234\r'.format(conf['pumpAddr'][pump]),'utf-8'))
    ser.write(bytes('{},WFR,{},{}\r'.format(conf['pumpAddr'][pump],speed,direction),'utf-8'))
    ser.write(bytes('{},WVO,{}\r'.format(conf['pumpAddr'][pump],volume),'utf-8'))
    ser.write(bytes('{},WON,1\r'.format(conf['pumpAddr'][pump]),'utf-8'))

    time_block = time.time()+volume/speed
    _ = setBlock(pump,time_block)

    ans = ser.read(1000)

    retc = return_class(
        measurement_type="pump_command",
        parameters={
            "command": "dispenseVolume",
            "parameters": {
                "volume": volume,
                "speed": speed,
                "pump": pump,
                "direction": direction,
                "time_block": time_block,
            },
        },
        data={'serial_response':ans},
    )
    return retc

@app.get("/pump/stopPump")
def stopPump(pump:int):
    #this stops a selected pump and returns the nessesary information the seed is recorded as zero and direction as -1
    #the reason for that is that i want to indicate that we manually stopped the pump
    ser.write(bytes('{},WON,0\r'.format(conf['pumpAddr'][pump]), 'utf-8'))
    time_block = time.time()
    _ = setBlock(pump,time_block)
    retc = return_class(
        measurement_type="pump_command",
        parameters={
            "command": "stopPump",
            "parameters": {
                "pump": pump,
                'speed': 0,
                'volume': 0,
                'direction': -1,
                "time_block": time_block,
            },
        },
        data=None,
    )
    return retc

@app.on_event("shutdown")
def shutdown():
    for i in range(14):
        stopPump(i)
    ser.close()
    retc = return_class(
        measurement_type="pump_command",
        parameters={"command": "shutdown"},
        data={'data':'shutdown'}
    )
    return retc


if __name__ == "__main__":

    p = pump()
    uvicorn.run(app, host="127.0.0.1", port=13370)
