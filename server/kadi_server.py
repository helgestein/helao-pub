from fastapi import FastAPI
from pydantic import BaseModel, validator, ValidationError
import json
import sys
sys.path.append('../config')
sys.path.append('../driver')
from kadi_driver import kadi
from mischbares_small import config
import uvicorn

#currently it seems like server needs to be restarted if there is an input error in any of your requests

app = FastAPI(title="KaDI4Mat Interface Driver V1",
    description="This is a very fancy data management server",
    version="1.0",)

class validator_class(BaseModel):
    ident: str
    title: str
    filed: str = '""'
    meta: str = '""'
    visibility: str

    @validator("visibility")
    def public_or_private(cls,v):
        if v != "public" and v != "private":
            raise ValidationError("visibility is not set to 'public' or 'private'")
        return v

    @validator("filed")
    def is_json(cls,v):
        try:
            json.loads(v)
        except:
            raise ValidationError("data is not a json")
        return v

    @validator("meta")
    def is_list_of_serialized_dicts(cls,v):
        if v != '""':
            for i in json.loads(v):
                assert type(i) == dict
        return v

@app.get("/kadi/addrecord")
def addRecord(ident:str,title:str,filed:str,meta:str,visibility:str='private'):
    print(meta)
    print(type(meta))
    print(json.loads(meta))
    val = validator_class(ident=ident,title=title,filed=filed,meta=meta,visibility=visibility)
    k.addRecord(ident,title,filed,meta,visibility)
    
@app.get("/kadi/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    val = validator_class(ident=identifier,title=title,visibility=visibility)
    k.addCollection(identifier,title,visibility)

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str):
    val = validator_class(ident=identCollection,title=identRecord)
    k.addRecord(identCollection,identRecord)

@app.get("/kadi/linkrecordtogroup")
def linkRecordToGroup(self,identGroup,identRecord):
    val = validator_class(ident=identGroup,title=identRecord)
    k.linkRecordToGroup(identGroup,identRecord)

@app.get("/kadi/linkcollectiontogroup")
def linkCollectionToGroup(self,identGroup,identCollection):
    val = validator_class(ident=identGroup,title=identCollection)
    k.linkCollectionToGroup(identGroup,identCollection)

if __name__ == '__main__':
    k = kadi(config['kadi'])
    uvicorn.run(app, host=config['servers']['kadiServer']['host'], 
                     port=config['servers']['kadiServer']['port'])