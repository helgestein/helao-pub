from kadi_apy import KadiManager
import json
import time
import os

class kadi():
    def __init__(self,conf):
        self.manager = KadiManager(token=conf['PAT'],host=conf['host'])

    def addRecord(self,ident,title,visibility='private'):
        #create a record
        #visibility must be 'public' or 'private'
        record = self.manager.record(identifier=ident,title=title,visibility=visibility,create=True)

    def addCollection(self,ident,title,visibility='private'):
        #create collection
        collection = self.manager.collection(identifier=ident,title=title,visibility=visibility,create=True)

    def addRecordToCollection(self,identCollection,identRecord):
        record = self.manager.record(identifier=identRecord)
        record.add_collection_link(self.manager.collection(identifier=identCollection).id)

    def linkRecordToGroup(self,identGroup,identRecord):
        record = self.manager.record(identifier=identRecord)
        record.add_group_role(identGroup,"editor")

    def linkCollectionToGroup(self,identGroup,identCollection):
        collection = self.manager.collection(identifier=identCollection)
        collection.add_group_role(identGroup,"editor")

    def recordExists(self,ident):
        #determine whether a record with the given identifier exists
        try:
            record = self.manager.record(identifier=ident)
        except:
            return False
        return True

    def collectionExists(self,ident):
        #determine whether a collection with the given identifier exists
        try:
            collection = self.manager.collection(identifier=ident)
        except:
            return False
        return True

    def addFileToRecord(self,identRecord,filed):
        #if file is a filepath, upload from that path, if file is a json, upload directly
        record = self.manager.record(identifier=identRecord)
        try: 
            json.loads(filed)
            record.upload_string_to_file(string=filed,file_name='{}_{}.json'.format(identRecord,time.time_ns()))
        except:
            record.upload_file(file_path=filed)

    def addMetadataToRecord(self,identRecord,meta):
        record = self.manager.record(identifier=identRecord)
        record.add_metadata(json.loads(meta),True)

    def downloadFilesFromRecord(self,ident,filepath):
        #download all files from record
        record = self.manager.record(identifier=ident)
        response = record.get_filelist(per_page=100).json()
        for i in range(response['_pagination']['total_pages']):
            page = record.get_filelist(page=i,per_page=100).json()
            for item in page['items']:
                record.download_file(item['id'],os.path.join(filepath,item['name']))

    def downloadFilesFromCollection(self,ident,filepath):
        #download all files from all records in collection
        collection = self.manager.collection(identifier=ident)
        response = collection.get_records(per_page=100).json()
        for i in range(response['_pagination']['total_pages']):
            page = collection.get_records(page=i,per_page=100).json()
            for item in page['items']:
                self.downloadFilesFromRecord(item['identifier'],filepath)

    def isFileInRecord(self,ident,filename):
        record = self.manager.record(identifier=ident)
        return record.has_file(filename)
