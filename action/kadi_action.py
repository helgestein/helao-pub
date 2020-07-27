#implement the action-server for kadi
import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, validator, ValidationError
import json
import requests

class validator_class(BaseModel):
    ident: str
    title: str
    filed: str = ''
    visibility: str
    meta: str = ''

    @validator("visibility")
    def public_or_private(cls,v):
        if v != "public" and v != "private":
            raise ValidationError("visibility is not set to 'public' or 'private'")
        return v

    @validator("filed","meta")
    def is_serialized_dict(cls,v):
        assert type(json.loads(v)) == dict or v == ''
        return v
        
app = FastAPI(title="Kadi server V1", 
description="This is a fancy kadi server", 
version="1.0")

@app.get("/data/addrecord")
def addRecord(ident:str,title:str,filed:str,visibility:str='private',meta:str=''): #filed is a json
    val = validator_class(ident=ident,title=title,filed=filed,visibility=visibility,meta=meta)
    requests.get("{}/kadi/addrecord".format(url), params={'ident':ident,'title':title,'filed':filed,'visibility':visibility,'meta':meta})

@app.get("/data/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    val = validator_class(ident=identifier,title=title,visibility=visibility)
    requests.get("{}/kadi/addcollection".format(url),params={'identifier':identifier,'title':title,'visibility':visibility})

@app.get("/data/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str,visibility:str='private',record:str=None):
    val = validator_class(ident=identCollection,title=identRecord,visibility=visibility)
    requests.get("{}/kadi/addrecordtocollection".format(url),params={'identCollection':identCollection,'identRecord':identRecord,'visibility':visibility,'record':record})


if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])

    uvicorn.run(app, host=config['servers']['dataServer']['host'], port=config['servers']['dataServer']['port'])
    print("instantiated kadi action")








