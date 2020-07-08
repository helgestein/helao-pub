#implement the action-server for kadi
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



app = FastAPI(title="Kadi server V1", 
    description="This is a fancy kadi server", 
    version="1.0")


class return_class(BaseModel):
    measurement_type: str = None
    parameters :dict = None
    data: dict = None

    def addRecord(ident,title,visibility,filed,meta = None): #filed is a json 
        requests.get("{}/kadi/addrecord".format(url)).json()

    def addCollection(identifier, title, visibility):
        requests.get("{}/kadi/addcollection".format(url)).json()

    def addRecordToCollection(identCollection,identRecord,visibility='public',record=None):
        requests.get("{}/kadi/addrecordtocollection".format(url)).json()


if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])
    
    uvicorn.run(app, host=config['servers']['dataServer']['host'], port=config['servers']['dataServer']['port'])
    print("instantiated kadi action")