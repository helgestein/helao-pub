#!/usr/bin/python3

from kadi_apy.lib.core import KadiAPI
from kadi_apy.lib.records import Record
from kadi_apy.lib.collections import Collection

class kadi():
    def __init__(self,conf):
        KadiAPI.token = conf['PAT']
        KadiAPI.host = conf['host']

    def addRecord(ident,title,visibility = 'public',filepath = None,meta = None):
        #create a record
        record = Record(identifier=ident, title=title, visibility=visibility)
        if not filepath == None:
            if not meta == None:
                #upload a file
                record.upload_file(file_path=pathToFile)
                #add metadatum
                record.add_metadatum(metadatum=meta, force=True)

    def addCollection(ident,title,visibility = 'public',filepath = None,meta = None):
        #create collection
        collection = Collection(identifier=ident, title=title, visibility=visibility)

    def addRecordToCollection(identCollection,identRecord,visibility='public'):
        collection = Collection(identifier=identCollection, title='title', visibility=visibility)
        record = Record(identifier=identRecord, title='title', visibility=visibility)
        #add record to collection
        collection.add_record(record_id=record.id)

if __name__ == '__main__':
    conf = dict(host = r"https://kadi4mat.iam-cms.kit.edu",
            PAT = r"98d7dfbcd77a9163dde2e8ca34867a4998ecf68bc742cf4e")
    k = kadi(conf)

    