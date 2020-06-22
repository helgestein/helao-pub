from fastapi import FastAPI
from pydantic import BaseModel
import json
import sys
sys.path.append('../config')
sys.path.append('../driver')

from driver.kadi_driver import kadi
import config.mischbares_small

app = FastAPI(title="KaDI4Mat Interface Driver V1",
    description="This is a very fancy datamanagement server",
    version="1.0",)

@app.get("/kadi/addrecord")
def addRecord(ident,title,visibility = 'public',filepath = None,meta = None)
    k.addRecord(ident,title,visibility,filepath,meta = None)
    pass

@app.get("/kadi/addcollection")
def addCollection(ident,title,visibility = 'public',filepath = None,meta = None)
    pass

@app.get("/kadi/addrecordtocollection")
def addRecordToCollection(identCollection,identRecord,visibility='public'):
    pass

if __name__ == '__main__':
    k = kadi(config.mischbares_small.config['kadi'])
    uvicorn.run(app, host=config['servers']['kadiServer']['host'], port=config['servers']['kadiServer']['port'])