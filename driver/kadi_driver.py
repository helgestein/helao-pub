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
            PAT = "acc833c1d1aa764b8923dd0bb519cd9aacc22c51332454e8")
    k = kadi(conf)

'''
from kadi_apy.lib.core import KadiAPI
from kadi_apy.lib.records import Record
from kadi_apy.lib.collections import Collection


host = r"https://kadi4mat.iam-cms.kit.edu"
PAT = "acc833c1d1aa764b8923dd0bb519cd9aacc22c51332454e8"
KadiAPI.token = PAT
KadiAPI.host = host

identifier = "just_a_string"
title ="my_title"
visibility = "private"
my_first_record = Record(identifier=identifier, title=title, visibility=visibility)

#erzeugt neuerdings:
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "C:\Users\Operator\anaconda3\envs\dev\lib\site-packages\kadi_apy\lib\records.py", line 27, in __init__
    self._start_session_item(id=id, **kwargs)
  File "C:\Users\Operator\anaconda3\envs\dev\lib\site-packages\kadi_apy\lib\core.py", line 104, in _start_session_item
    raise KadiApyIdentifierError
kadi_apy.lib.exceptions.KadiApyIdentifierError
'''