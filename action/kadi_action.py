#implement the action-server for kadi
import sys
sys.path.append('../driver')
sys.path.append('../config')
sys.path.append('../server')
from mischbares_small import config
import uvicorn
from fastapi import FastAPI
import json
import requests
import os

app = FastAPI(title="Kadi server V1", 
description="This is a fancy kadi server", 
version="1.0")

@app.get("/data/addrecord")
def addRecord(ident:str,title:str,visibility:str='private'): #filed is a json
    requests.get("{}/kadi/addrecord".format(url), params={'ident':ident,'title':title,'visibility':visibility})
    requests.get("{}/kadi/linkrecordtogroup".format(url), params={'identGroup':config['kadi']['group'],'identRecord':ident})

@app.get("/data/addcollection")
def addCollection(identifier:str,title:str,visibility:str='private'):
    requests.get("{}/kadi/addcollection".format(url),params={'identifier':identifier,'title':title,'visibility':visibility})
    requests.get("{}/kadi/linkcollectiontogroup".format(url),params={'identGroup':config['kadi']['group'],'identCollection':identifier})


@app.get("/data/addrecordtocollection")
def addRecordToCollection(identCollection:str,identRecord:str):
    requests.get("{}/kadi/addrecordtocollection".format(url),params={'identCollection':identCollection,'identRecord':identRecord})
    requests.get("{}/kadi/linkrecordtogroup".format(url),params={'identGroup':config['kadi']['group'],'identRecord':identRecord})

@app.get("/data/addfiletorecord")
def addFileToRecord(identRecord:str,filed:str):
    #if file is a filepath, upload from that path, if file is a json, upload directly
    requests.get("{}/kadi/addfiletorecord".format(url),params={'identRecord':identRecord,'filed':filed})

@app.get("/data/addmetadatatorecord")
def addMetadataToRecord(identRecord:str,meta:str):
    requests.get("{}/kadi/addmetadatatorecord".format(url),params={'identRecord':identRecord,'meta':meta})

@app.get("/data/recordexists")
def recordExists(ident:str):
    #determine whether a record with the given identifier exists
    return requests.get("{}/kadi/recordexists".format(url),params={'ident':ident}).json()

@app.get("/data/collectionexists")
def collectionExists(ident:str):
    #determine whether a collection with the given identifier exists
    return requests.get("{}/kadi/collectionexists".format(url),params={'ident':ident}).json()

@app.get("/data/reformatmetadata")
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

@app.get("/data/extractdata")
def extractData(metadata:dict):
    #pull out whatever is under the lowest key called "data" in a nested set of dictionaries and lists of dictionaries
    #obsoleted by the fact that records will now comprise multiple actions
    if 'data' in metadata:
        if type(metadata['data']) == dict:
            return extractData(metadata['data'])
        if type(metadata['data']) == list:
                return [extractData(i) for i in metadata['data']]
        return metadata['data']
    return None

@app.get("/data/findfilepath")
def findFilepath(metadata:dict):
    #search dictionary for filepaths
    #obsoleted by the fact that records will now comprise multiple actions
    safepaths = []
    filenames = []
    for key,val in metadata.items():
        if type(val) == dict:
            lists = findFilepath(val)
            safepaths += lists[0]
            filenames += lists[1]
        if type(val) == list:
            for i in val:
                if type(i) == dict:            
                    lists = findFilepath(i)
                    safepaths += lists[0]
                    filenames += lists[1]
        if key == "safepath":
            safepaths.append(val)
        if key == "filename":
            filenames.append(val)
    #filter duplicates
    csafepaths = []
    cfilenames = []
    for i,j in zip(safepaths,filenames):
        if i not in csafepaths or j not in cfilenames:
            csafepaths.append(i)
            cfilenames.append(j)
    return (csafepaths,cfilenames)
        

@app.get("/data/makerecordfromfile")
def makeRecordFromFile(filename:str,filepath:str,visibility:str='private'):
    #obsoleted by the fact that records will now comprise multiple actions
    data = json.load(open(os.path.join(filepath,filename),'r'))
    filed = json.dumps(extractData(data))
    meta = json.dumps(reformatMetadata(data))
    ident = filename.split("_")[0]
    title = filename[:-5]
    if not recordExists(ident):
        addRecord(ident,title,visibility)
        addFileToRecord(ident,data)
        addMetadataToRecord(ident,meta)
        paths = findFilepath(data)
        for i,j in zip(paths[0],paths[1]):
            addFileToRecord(ident,os.path.join(i,j))
    else:
        print("record already exists")

@app.get("/data/downloadfilesfromrecord")
def downloadFilesFromRecord(ident:str,filepath:str):
    #download all files from record
    requests.get("{}/kadi/downloadfilesfromrecord".format(url),params={'ident':ident,'filepath':filepath})

@app.get("/data/downloadfilesfromcollection")
def downloadFilesFromCollection(ident:str,filepath:str):
    #download all files from all records in collection
    requests.get("{}/kadi/downloadfilesfromcollection".format(url),params={'ident':ident,'filepath':filepath})
    
@app.get("/data/isfileinrecord")
def isFileInRecord(ident:str,filename:str):
    return requests.get("{}/kadi/downloadfilesfromcollection".format(url),params={'ident':ident,'filepath':filename}).json()

@app.get("/data/assimilatefile")
def assimilateFile(filename:str,filepath:str):
#assimilate file into our kadi system, defined such that each measurement area is a record and each substrate is a collection
    substrate,ma = filename.split("_")[1:3]
    recordname = substrate+"_"+ma
    collectionname = "substrate_"+substrate
    if not collectionExists(collectionname):
        addCollection(collectionname,collectionname,"private")
    if not recordExists(recordname):
        addRecord(recordname,recordname,"private")
        addRecordToCollection(collectionname,recordname)
    if not isFileInRecord(recordname,filename):
        addFileToRecord(recordname,os.path.join(filepath,filename))
        paths = findFilepath(json.load(open(os.path.join(filepath,filename),'r')))
        for i,j in zip(paths[0],paths[1]):
            addFileToRecord(recordname,os.path.join(i,j))
    else:
        print("file already assimilated")

if __name__ == "__main__":
    url = "http://{}:{}".format(config['servers']['kadiServer']['host'], config['servers']['kadiServer']['port'])

    uvicorn.run(app, host=config['servers']['dataServer']['host'], port=config['servers']['dataServer']['port'])
    print("instantiated kadi action")








