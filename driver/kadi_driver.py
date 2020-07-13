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

    def addRecord(self, ident, title, filed, visibility='private', meta=''): #filed is a json 
        #create a record
        #visibility must be 'public' or 'private'
        # if not '', meta must be serialized dict
        # the value of the dictionary can be either 'list, number, string and dict' 
        record = Record(identifier=ident, title=title, visibility=visibility)
        record.upload_string_to_file(string=filed,file_name='{}_{}.json'.format(ident,time.time_ns()))
        #add metadatum#
        if meta != '':
            df = pandas.json_normalize(json.loads(meta), sep='_')
            meta = df.to_dict(orient='records')[0]
            record.add_metadatum(metadatum=meta, force=True)

    def addCollection(self, identifier, title, visibility):
        #create collection
        collection = Collection(identifier=ident,title=title,visibility=visibility)

    def addRecordToCollection(self,identCollection,identRecord,visibility='public',record=None):
        collection = Collection(identifier=identCollection, title='title', visibility=visibility)
        if record == None:
            record = Record(identifier=identRecord, title='title', visibility=visibility)
        #add record to collection
        collection.add_record(record_id=record.id)