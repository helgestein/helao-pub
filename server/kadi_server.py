from fastapi import FastAPI
import json
import sys
import uvicorn
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
from kadi_driver import kadi
from mischbares_small import config
#config = import_module(sys.argv[1]).config


#currently it seems like server needs to be restarted if there is an input error in any of your requests

app = FastAPI(title="KaDI4Mat Interface Driver V1",
    description="This is a very fancy data management server",
    version="1.0")

@app.get("/kadi/addrecord")
def addRecord(ident:str,title:str,visibility:str='private'):
    k.addRecord(ident,title,visibility)
    
@app.get("/kadi/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    k.addCollection(identifier,title,visibility)

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str):
    k.addRecordToCollection(identCollection,identRecord)

@app.get("/kadi/linkrecordtogroup")
def linkRecordToGroup(identGroup:str,identRecord:str):
    k.linkRecordToGroup(identGroup,identRecord)

@app.get("/kadi/linkcollectiontogroup")
def linkCollectionToGroup(identGroup:str,identCollection:str):
    k.linkCollectionToGroup(identGroup,identCollection)

@app.get("/kadi/recordexists")
def recordExists(ident:str):
    #determine whether a record with the given identifier exists
    return k.recordExists(ident)

@app.get("/kadi/collectionexists")
def collectionExists(ident:str):
    #determine whether a collection with the given identifier exists
    return k.collectionExists(ident)

@app.get("/kadi/isfileinrecord")
def isFileInRecord(ident:str,filename:str):
    return k.isFileInRecord(ident,filename)

@app.get("/kadi/addfiletorecord")
def addFileToRecord(identRecord:str,filed:str):
    #if file is a filepath, upload from that path, if file is a json, upload directly
    k.addFileToRecord(identRecord,filed)

@app.get("/kadi/addmetadatatorecord")
def addMetadataToRecord(identRecord:str,meta:str):
    k.addMetadataToRecord(identRecord,meta)

@app.get("/kadi/downloadfilesfromrecord")
def downloadFilesFromRecord(ident:str,filepath:str):
    #download all files from record
    k.downloadFilesFromRecord(ident,filepath)

@app.get("/kadi/downloadfilesfromcollection")
def downloadFilesFromCollection(ident:str,filepath:str):
    #download all files from all records in collection
    k.downloadFilesFromCollection(ident,filepath)

if __name__ == '__main__':
    k = kadi(config['kadi'])
    uvicorn.run(app, host=config['servers']['kadiServer']['host'], 
                     port=config['servers']['kadiServer']['port'])