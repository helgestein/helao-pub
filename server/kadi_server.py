from fastapi import FastAPI
from pydantic import BaseModel
import json
import sys
sys.path.append('../config')
sys.path.append('../driver')
from kadi_driver import kadi
from mischbares_small import config
import uvicorn

app = FastAPI(title="KaDI4Mat Interface Driver V1",
    description="This is a very fancy data management server",
    version="1.0",)

@app.get("/kadi/addrecord")
def addRecord(ident:str,title:str,visibility:str,filed:str,meta:str):
    k.addRecord(ident=ident,title=title,visibility=visibility,filed=filed,meta=meta)
    
@app.get("/kadi/addcollection")
def addCollection(identifier:str,title:str,visibility:str = 'private'):
    k.addCollection(identifier, title, visibility)

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str,visibility: str='public',record: str=None):
    k.addRecord(identCollection,identRecord,visibility,record)

if __name__ == '__main__':
    k = kadi(config['kadi'])
    uvicorn.run(app, host=config['servers']['kadiServer']['host'], 
                     port=config['servers']['kadiServer']['port'])