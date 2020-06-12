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






if __name__ == "__main__":

    p = Mecademic()
    uvicorn.run(app, host="127.0.0.1", port=13370)