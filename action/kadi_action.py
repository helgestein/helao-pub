#implement the action-server for kadi
import sys
sys.path.append(r'../driver')
sys.path.append(r'../config')
sys.path.append(r'../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
<<<<<<< HEAD
from pydantic import BaseModel, validator
import json
import requests


<<<<<<< Updated upstream
class UserModel(BaseModel):
    name: str
    username: str
    password1: str
    password2: str

    @validator('name')
    def public_or_private(cls, v):
        if v != "public" or != "private":
            raise ValueError('must be in the list')
        return v

    @validator() 


=======
    @validator("filed", "meta")
    def is_serialized_dict(cls,v):
        assert type(json.loads(v)) == dict
        return v

        
>>>>>>> Stashed changes
=======
from pydantic import BaseModel,validator,ValidationError
import json
import requests

class validator_class(BaseModel):
    ident: str
    title: str
    visibility: str
    filed: str = ''
    meta: str = ''

    @validator("visibility")
    def public_or_private(cls,v):
        if v != "public" and v != "private":
            raise ValidationError("visibility is not set to 'public' or 'private'")
        return v

    @validator("filed","meta")
    def is_serialized_dict(cls,v):
        try:
            if type(json.loads(v)) != dict and v != '':
                raise ValidationError('file or metadata cannot be loaded by json')
        except:
            raise ValidationError('file or metadata is not a serialized dict')
        return v
        
        
>>>>>>> 2861bbc280089bf511dbaed093effd1c9e279f49
app = FastAPI(title="Kadi server V1", 
description="This is a fancy kadi server", 
version="1.0")

@app.get("/data/addrecord")
<<<<<<< Updated upstream
def addRecord(ident:str,title:str,visibility:str,filed:str,meta:str= None): #filed is a json
<<<<<<< HEAD
=======
def addRecord(ident:str,title:str,visibility:str,filed:str,meta:str= ''): #filed is a json
    val = validator_class(ident=ident,title=title,visibility=visibility,filed=filed,meta=meta)

>>>>>>> Stashed changes
=======
    val = validator_class(ident=ident,title=title,visibility=visibility,filed=filed,meta=meta)
>>>>>>> 2861bbc280089bf511dbaed093effd1c9e279f49
    requests.get("{}/kadi/addrecord".format(url), params={'ident': ident,'title': title, 'visibility': visibility,
                                                         'filled':filed,'meta':meta}).json()

@app.get("/data/addcollection")
def addCollection(identifier:str,title:str,visibility:str):
    val = validator_class(ident=identifier,title=title,visibility=visibility)
    requests.get("{}/kadi/addcollection".format(url),params={'identifier':identifier,'title':title,'visibility':visibility}).json()

@app.get("/data/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str,visibility:str='public',record:str=None):
    val = validator_class(ident=identCollection,title=identRecord,visibility=visibility)
    requests.get("{}/kadi/addrecordtocollection".format(url),params={'identCollection':identCollection,'identRecord':identRecord,'visibility':visibility,'record':record}).json()


if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])
    
    uvicorn.run(app, host=config['servers']['dataServer']['host'], port=config['servers']['dataServer']['port'])
    print("instantiated kadi action")








