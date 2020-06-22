from kadi_apy.lib.core import KadiAPI
from kadi_apy.lib.records import Record
from kadi_apy.lib.collections import Collection
import json
import time
import pandas

class kadi():
    def __init__(self,conf):
        KadiAPI.token = conf['PAT']
        KadiAPI.host = conf['host']

    def addRecord(ident,title,visibility,filed,meta = None):
        #create a record
        record = Record(identifier=ident, title=title, visibility=visibility)
        record.upload_string_to_file(string=json.dumps(filed),file_name='{}_{}.json'.format(ident,time.time_ns()))
        #add metadatum
        df = pd.io.json.json_normalize(d, sep='_')
        meta_flat = df.to_dict(orient='records')[0]
        record.add_metadatum(metadatum=meta_flat, force=True)

    def addCollection(identifier, title, visibility):
        #create collection
        collection = Collection(identifier=ident, title=title, visibility=visibility)

    def addRecordCollection(ident,title,visibility,filed,meta = None):
        #create a record
        record = Record(identifier=ident, title=title, visibility=visibility)
        record.upload_string_to_file(string=json.dumps(filed),file_name='{}_{}.json'.format(ident,time.time_ns()))
        #add metadatum
        df = pd.io.json.json_normalize(d, sep='_')
        meta_flat = df.to_dict(orient='records')[0]
        record.add_metadatum(metadatum=meta_flat, force=True)


    def addRecordToCollection(identCollection,identRecord,visibility='public',record=None):
        collection = Collection(identifier=identCollection, title='title', visibility=visibility)
        if record == None:
            record = Record(identifier=identRecord, title='title', visibility=visibility)
        #add record to collection
        collection.add_record(record_id=record.id)