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

    def addRecord(self,ident,title,filed,visibility='private',meta=''):
        #create a record
        #visibility must be 'public' or 'private'
        # if not '', meta must be serialized dict, filed will likely always be a serialized dict but does not need to be
        record = Record(identifier=ident,title=title,visibility=visibility)
        record.upload_string_to_file(string=filed,file_name='{}_{}.json'.format(ident,time.time_ns()))
        #metadata is currently turned off because it is broken



    def addCollection(self,ident,title,visibility='private'):
        #create collection
        collection = Collection(identifier=ident,title=title,visibility=visibility)

    def addRecordToCollection(self,identCollection,identRecord,visibility='private',record_id=None):
        collection = Collection(identifier=identCollection, title='title',visibility=visibility)
        if record_id == None:
            record_id = Record(identifier=identRecord,title='title',visibility=visibility).id
        #add record to collection
        collection.add_record(record_id=record_id)