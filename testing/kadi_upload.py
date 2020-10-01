import os
import sys
sys.path.append("../action")
import kadi_action as ka
from mischbares_small import config
import requests
import json

if __name__ == "__main__":
    soe = ["data/addcollection_0"]
    params = dict(addcollection_0=dict(identifier="ramandemo",title="dry run of my raman orchestrator"))
    #ka.addCollection("demo","uploading a bunch of initial echem data to see how it looks","private")
    i=0
    for filename in os.listdir("C:/Users/Operator/Documents/data"):
        ident = filename.split("_")[0]
        #if not ka.recordExists(ident):
            #ka.makeRecordFromFile(filename,r"D:\kadiupload",visibility="private")
        soe.append("data/makerecordfromfile_{}".format(i))
        params.update({"makerecordfromfile_{}".format(i):dict(filename=filename,filepath="C:/Users/Operator/Documents/data")})
        #ka.addRecordToCollection("demo",ident)
        soe.append("data/addrecordtocollection_{}".format(i))
        params.update({"addrecordtocollection_{}".format(i):dict(identCollection="ramandemo",identRecord=ident)})
        i += 1
        if i % 100 == 0:
            experiment = dict(soe=soe,params=params,meta=dict(substrate="dry",ma="dry"))
            requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
            soe = []
            params = {}
        if i == 100:
            requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"infiniteLoop"),params= None)