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
        
app = FastAPI(title="Kadi server V1", 
description="This is a fancy kadi server", 
version="1.0")

@app.get("/data/addrecord")
def addRecord(ident:str,title:str,filed:str,meta:str,visibility:str='private'): #filed is a json
    val = validator_class(ident=ident,title=title,filed=filed,meta=meta,visibility=visibility)
    requests.get("{}/kadi/addrecord".format(url), params={'ident':ident,'title':title,'filed':filed,'meta':meta,'visibility':visibility})

@app.get("/data/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    val = validator_class(ident=identifier,title=title,visibility=visibility)
    requests.get("{}/kadi/addcollection".format(url),params={'identifier':identifier,'title':title,'visibility':visibility})
    requests.get("{}/kadi/linkcollectiontogroup".format(url),params={'identGroup':config['kadi']['group'],'identCollection':identifier})


@app.get("/data/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str):
    val = validator_class(ident=identCollection,title=identRecord)
    requests.get("{}/kadi/addrecordtocollection".format(url),params={'identCollection':identCollection,'identRecord':identRecord})


@app.get("/data/reformatmetadata")
def reformatMetadata(metadata:dict):
    #take a json-ed metadata dictionary as input, and convert it into a forman amenable to kadi.
    metadata = json.loads(metadata)
    newmeta = []
    for key,val in metadata.items():
        if key != 'data' or type():
            newmeta.append({'key':key,'type':str(type(val))[8:-2],
                'value': reformatMetadata(val) if type(val) == dict else [{'type':str(type(i))[8:-2],'value':i if type(i) != dict else reformatMetadata(i)} for i in val[:5]] if type(val) == list or str(type(val))[8:-2]  == 'numpy.ndarray' else val})
    return newmeta

@app.get("/data/extractdata")
def extractData(metadata:dict):
    if 'data' in metadata:
        if type(metadata['data']) == dict:
            return extractData(metadata['data'])
        if type(metadata['data']) == list:
                return [extractData(i) for i in metadata['data']]
    return metadata


@app.get("/data/makerecordfromfile")
def makeRecordFromFile(filename,filepath,visibility='private'):
    try:
        filed = json.dumps(data['data']['data'])
    except:
        filed = json.dumps(data['data'])
    meta = json.dumps(reformatMetadata(data))
    addRecord(ident,title,filed,meta,visibility)

if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])

    uvicorn.run(app, host=config['servers']['dataServer']['host'], port=config['servers']['dataServer']['port'])
    print("instantiated kadi action")








