from fastapi import FastAPI
from pydantic import BaseModel, validator, ValidationError
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

class validator_class(BaseModel):
    ident: str
    title: str
    filed: str = ''
    visibility: str = 'private'
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

@app.get("/kadi/addrecord")
def addRecord(ident:str,title:str,visibility:str,filed:str,meta:str=None):
    val = validator_class(ident=ident,title=title,filed=filed,visibility=visibility) if meta == None else validator_class(ident=ident,title=title,filed=filed,visibility=visibility,meta=meta)
    k.addRecord(ident,title,visibility,filed,meta)
    
@app.get("/kadi/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    val = validator_class(ident=identifier,title=title,visibility=visibility)
    k.addCollection(identifier,title,visibility)

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str,visibility:str='public',record:str=None):
    val = validator_class(ident=identCollection,title=identRecord,visibility=visibility)
    k.addRecord(identCollection,identRecord,visibility,record)

if __name__ == '__main__':
    k = kadi(config['kadi'])
    uvicorn.run(app, host=config['servers']['kadiServer']['host'], 
                     port=config['servers']['kadiServer']['port'])