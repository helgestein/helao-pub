#!/usr/bin/python3

from kadi_apy.lib.core import KadiAPI
from kadi_apy.lib.records import Record
from kadi_apy.lib.collections import Collection


host = r"https://kadi4mat.iam-cms.kit.edu"
PAT = 


def execute():

    KadiAPI.token = PAT
    KadiAPI.host = host

    identifier = "just_a_string"
    title ="my_title"
    visibility = "private"

    #create a record
    my_first_record = Record(identifier=identifier, title=title, visibility=visibility)

    pathToFile = "./foo.bar"

    #upload a file
    my_first_record.upload_file(file_path=pathToFile)


    metadatum_new = {
        "type": "float",
        "unit": "km",
        "key": "length",
        "value": 5.0,
    }
    #add metadatum
    my_first_record.add_metadatum(metadatum=metadatum_new, force=True)


    #create collection
    my_first_collection = Collection(identifier="collection_name_1", title="collection_1", visibility=visibility)

    my_second_collection = Collection(identifier="collection_name_2", title="collection_2", visibility=visibility)

    #add record to collection
    my_first_collection.add_record(record_id=my_first_record.id)
    my_second_collection.add_record(record_id=my_first_record.id)

if __name__ == '__main__':
    execute()
