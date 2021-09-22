import sys
import uvicorn
from fastapi import FastAPI
import json
import requests
import os
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]

app = FastAPI(title="Kadi server V1", 
description="This is a fancy kadi server", 
version="1.0")

@app.get("/kadi/addrecord")
def addRecord(ident:str,title:str,visibility:str='private'): #filed is a json
    requests.get("{}/kadiDriver/addrecord".format(url), params={'ident':ident,'title':title,'visibility':visibility})
    requests.get("{}/kadiDriver/linkrecordtogroup".format(url), params={'identGroup':config[serverkey]['group'],'identRecord':ident})

@app.get("/kadi/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    requests.get("{}/kadiDriver/addcollection".format(url),params={'identifier':identifier,'title':title,'visibility':visibility})
    requests.get("{}/kadiDriver/linkcollectiontogroup".format(url),params={'identGroup':config[serverkey]['group'],'identCollection':identifier})

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str):
    requests.get("{}/kadiDriver/addrecordtocollection".format(url),params={'identCollection':identCollection,'identRecord':identRecord})

@app.get("/kadi/addfiletorecord")
def addFileToRecord(identRecord:str,filed:str):
    #if file is a filepath, upload from that path, if file is a json, upload directly
    requests.get("{}/kadiDriver/addfiletorecord".format(url),params={'identRecord':identRecord,'filed':filed})

@app.get("/kadi/addmetadatatorecord")
def addMetadataToRecord(identRecord:str,meta:str):
    requests.get("{}/kadiDriver/addmetadatatorecord".format(url),params={'identRecord':identRecord,'meta':meta})

@app.get("/kadi/recordexists")
def recordExists(ident:str):
    #determine whether a record with the given identifier exists
    return requests.get("{}/kadiDriver/recordexists".format(url),params={'ident':ident}).json()

@app.get("/kadi/collectionexists")
def collectionExists(ident:str):
    #determine whether a collection with the given identifier exists
    return requests.get("{}/kadiDriver/collectionexists".format(url),params={'ident':ident}).json()

@app.get("/kadi/downloadfilesfromrecord")
def downloadFilesFromRecord(ident:str,filepath:str):
    #download all files from record
    requests.get("{}/kadiDriver/downloadfilesfromrecord".format(url),params={'ident':ident,'filepath':filepath})

@app.get("/kadi/downloadfilesfromcollection")
def downloadFilesFromCollection(ident:str,filepath:str):
    #download all files from all records in collection
    requests.get("{}/kadiDriver/downloadfilesfromcollection".format(url),params={'ident':ident,'filepath':filepath})
    
@app.get("/kadi/isfileinrecord")
def isFileInRecord(ident:str,filename:str):
    return requests.get("{}/kadiDriver/isfileinrecord".format(url),params={'ident':ident,'filename':filename}).json()

@app.get("/kadi/uploadhdf5")
def uploadHDF5(filename:str,filepath:str):
    #check if proper collection exists
    cname = "stein_substrate_"+filename.split('_')[1]
    rname = filename[:-5]
    if not collectionExists(cname):
        addCollection(cname,cname[6:])
    #create proper record
    addRecord(rname,rname)
    addRecordToCollection(cname,rname)
    #upload hdf5 to record
    addFileToRecord(rname,os.path.join(filepath,filename))
    #i will need to add metadata capability for this, 
    #but want to have another conversation with helge and fuzhan first
    #so probably will not implement this feature on the first pass
    return "upload successful"

@app.get("/kadi/reformatmetadata")
def reformatMetadata(metadata:dict):
    #take a metadata dictionary as input, and convert it into a format amenable to kadi.
    #also omit what we will grab with extractData
    #obsoleted by the fact that records will now comprise multiple actions
    newmeta = []
    for key,val in metadata.items():
        if (key != 'data' or type(val) == dict and 'data' in val):
            if val == None:
                val = "None"
            newmeta.append({'key':key,'type':str(type(val))[8:-2],
                'value': reformatMetadata(val) if type(val) == dict else [{'type':str(type(i))[8:-2],'value':i  if type(i) != dict else reformatMetadata(i)} for i in val[:5]] if type(val) == list or str(type(val))[8:-2]  == 'numpy.ndarray' else val})
    return newmeta


if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], port=config['servers'][serverkey]['port'])
    print("instantiated kadi action")