# shell: uvicorn motion_server:app --reload

import os, sys

if __package__:
    # can import directly in package mode
    print("importing config vars from package path")
else:
    # interactive kernel mode requires path manipulation
    cwd = os.getcwd()
    pwd = os.path.dirname(cwd)
    print(pwd)
    if os.path.basename(pwd) == "HELAO":
        sys.path.insert(0, pwd)
    if pwd in sys.path or os.path.basename(cwd) == "HELAO":
        print("importing config vars from sys.path")
    else:
        raise ModuleNotFoundError("unable to find config vars, current working directory is {}".format(cwd))

from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
# from gamry_driver import *
from driver.gamry_simulate import *
from fastapi import Query
from typing import List

app = FastAPI()


class return_class(BaseModel):
    measurement_type: str
    parameters: dict
    data: list


@app.get("/potentiostat/get/potential_ramp")
async def pot_potential_ramp_wrap(
    Vinit: float, Vfinal: float, ScanRate: float, SampleRate: float
):
    return return_class(**poti.potential_ramp(Vinit, Vfinal, ScanRate, SampleRate))


@app.get("/potentiostat/get/potential_cycle")
async def pot_potential_ramp_wrap(
    Vinit: float,
    Vfinal: float,
    Vapex1: float,
    Vapex2: float,
    ScanInit: float,
    ScanApex: float,
    ScanFinal: float,
    HoldTime0: float,
    HoldTime1: float,
    HoldTime2: float,
    Cycles: int,
    SampleRate: float,
    control_mode: str,
):
    return return_class(
        **poti.potential_cycle(
            Vinit,
            Vfinal,
            Vapex1,
            Vapex2,
            ScanInit,
            ScanApex,
            ScanFinal,
            HoldTime0,
            HoldTime1,
            HoldTime2,
            Cycles,
            SampleRate,
            control_mode,
        )
    )


@app.get("/potentiostat/get/eis")
async def eis_(start_freq: float, end_freq: float, points: int, pot_offset: float = 0):
    return return_class(**poti.eis(start_freq, end_freq, points, pot_offset))


@app.get("/potentiostat/get/status")
def status_wrapper():
    return return_class(
        measurement_type="status_query",
        parameters={"query": "potentiostat"},
        data=[poti.status()],
    )


@app.get("/potentiostat/get/signal_arr")
async def signal_array_(Cycles: int, SampleRate: float, arr: str):
    arr = [float(i) for i in arr.split(",")]
    return return_class(**poti.signal_array(Cycles, SampleRate, arr))


@app.on_event("shutdown")
def shutdown_event():
    # this gets called when the server is shut down or reloaded to ensure a clean
    # disconnect ... just restart or terminate the server
    poti.close_connection()
    loop.close()
    return {"shutdown"}


if __name__ == "__main__":
    poti = gamry()
    # makes this runnable and debuggable in VScode
    # letters of the alphabet GAMRY => G6 A0 M12 R17 Y24
    uvicorn.run(app, host=FASTAPI_HOST, port=ECHEM_PORT)

    # http://127.0.0.1:8003/potentiostat/get/potential_ramp?Vinit=0&Vfinal=0.2&ScanRate=0.01&SampleRate=0.01
