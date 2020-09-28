import os
import sys
sys.path.append("../action")
import kadi_action as ka
from mischbares_small import config


if __name__ == "__main__":
    soe = ["data/addCollection_0"]
    params = dict("addCollection_0"=dict(identifier="",title=""))
    #ka.addCollection("demo","uploading a bunch of initial echem data to see how it looks","private")
    i=0
    for filename in os.listdir(r"C:\"):
        ident = filename.split("_")[0]
        #if not ka.recordExists(ident):
            #ka.makeRecordFromFile(filename,r"D:\kadiupload",visibility="private")
        soe.append("data/makeRecordFromFile_{}".format(i))
        params.update(dict("makeRecordFromFile_{}".format(i)=dict(filename=filename,filepath="")))
        #ka.addRecordToCollection("demo",ident)
        soe.append("data/addRecordToCollection_{}".format(i))
        params.update(dict("addRecordToCollection_{}".format(i)=dict(identCollection="",identRecord=ident)))
        i += 1