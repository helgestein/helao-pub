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

    def addRecord(self,ident,title,filed,visibility='private',meta=None): #filed is a json 
        #create a record
        #visibility must be 'public' or 'private'
        #if not None, meta must be serialized dict
        #I think that this probably works, but that there may still be some typing confusion. If filed is already a json, why do we need to upload it as json.dumps(filed)?
        record = Record(identifier=ident, title=title, visibility=visibility)
        record.upload_string_to_file(string=json.dumps(filed),file_name='{}_{}.json'.format(ident,time.time_ns()))
        #add metadatum#
        if meta != None:
            df = pandas.json_normalize(json.loads(meta), sep='_')
            meta = df.to_dict(orient='records')[0]
            record.add_metadatum(metadatum=meta, force=True)

    def addCollection(self,ident,title,visibility):
        #create collection
        collection = Collection(identifier=ident,title=title,visibility=visibility)

    def addRecordToCollection(self,identCollection,identRecord,visibility='public',record=None):
        collection = Collection(identifier=identCollection, title='title', visibility=visibility)
        if record == None:
            record = Record(identifier=identRecord, title='title', visibility=visibility)
        #add record to collection
        collection.add_record(record_id=record.id)