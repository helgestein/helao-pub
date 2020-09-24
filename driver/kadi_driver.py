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

    def addRecord(self,ident,title,filed,meta,visibility='private'):
        #create a record
        #visibility must be 'public' or 'private'
        #meta must be serialized dict
        record = Record(identifier=ident,title=title,visibility=visibility,create=True)
        record.upload_string_to_file(string=filed,file_name='{}_{}.json'.format(ident,time.time_ns()))
        record.add_metadata(json.loads(meta),True)

    def addCollection(self,ident,title,visibility='private'):
        #create collection
        collection = Collection(identifier=ident,title=title,visibility=visibility,create=True)

    def addRecordToCollection(self,identCollection,identRecord):
        collection = Collection(identifier=identCollection)
        collection.add_record(record_id=Record(identifier=identRecord).id)

    def linkRecordToGroup(self,identGroup,identRecord):
        record = Record(identifier=identRecord)
        record.add_group(identGroup)

    def linkCollectionToGroup(self,identGroup,identCollection):
        collection = Collection(identifier=identCollection)
        collection.add_group(identGroup)

