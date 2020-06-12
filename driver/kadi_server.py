from kadi_driver import kadi
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI(title="KaDI4Mat Interface Driver V1",
    description="This is a very fancy datamanagement server",
    version="1.0",)

@app.get("/kadi/addrecord")
def addRecord(ident,title,visibility = 'public',filepath = None,meta = None)
    pass

@app.get("/kadi/addcollection")
def addCollection(ident,title,visibility = 'public',filepath = None,meta = None)
    pass

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection,identRecord,visibility='public'):
    pass

if __name__ == '__main__':
    conf = dict(host = r"https://kadi4mat.iam-cms.kit.edu",
            PAT = r"98d7dfbcd77a9163dde2e8ca34867a4998ecf68bc742cf4e")
    k = kadi(conf)
    uvicorn.run(app, host="127.0.0.1", port=13371)

