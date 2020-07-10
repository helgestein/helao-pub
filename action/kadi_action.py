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

@app.get("/data/addrecord")
def addRecord(ident:str,title:str,visibility:str,filed:str,meta:str= None): #filed is a json
    requests.get("{}/kadi/addrecord".format(url), params={'ident': ident,'title': title, 'visibility': visibility,
                                                         'filled':filed,'meta':meta}).json()

@app.get("/data/addcollection")
def addCollection(identifier:str,title:str,visibility:str):
    requests.get("{}/kadi/addcollection".format(url),params={'identifier':identifier,'title':title,'visibility':visibility}).json()

@app.get("/data/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str,visibility:str='public',record:str=None):
    requests.get("{}/kadi/addrecordtocollection".format(url),params={'identCollection':identCollection,'identRecord':identRecord,'visibility':visibility,'record':record}).json()


if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])
    
    uvicorn.run(app, host=config['servers']['dataServer']['host'], port=config['servers']['dataServer']['port'])
    print("instantiated kadi action")