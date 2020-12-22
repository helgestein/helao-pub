import sys
sys.path.append('../driver')
from kadi_driver import kadi
import requests
from kadi_apy.lib.core import KadiAPI
from kadi_apy.lib.records import Record
from kadi_apy.lib.collections import Collection
import time
import json
import os
from alive_progress import alive_bar


#this script will test a variety of functions in the Kadi data management system of KIT, 
#and it's implementation in the helao lab management software in development by the Stein group at KIT.
#what follows are options that should be specified prior to running the script:
KadiAPI.token = r"52891e3a29fdf810abccc5ceda33b90a06e78ca25bcfac39" #personal access token for Kadi. use your own if you have one.
KadiAPI.host = r"https://polis-kadi4mat.iam-cms.kit.edu" #website at which relevant instance of Kadi is hosted
unique = 'homeether4' #each time this script is run, a unique identifier must be provided. 
#because deleted records in Kadi are not immediately purged and cannot be overwritten, 
#this ensures that each run will use records of a different identifier and not crash from trying to overwrite something
yourname = 'jack' #just put your name here, will be part of the record name, so we know who ran the script
n = 1000 #how many times you want to repeat each operation in your test.
filepath = 'C:/Users/jkflowers/Desktop/downloadpath' #need a directory from which to upload and download files.
#large numbers of copies of whatever file you upload may be downloaded to this path,
# so you should probably make a new directory for this
filename = 'Hgrid.json' #name of the file you want to upload when testing file uploading and downloading,
#should be in directory named in filepath above
filesize = '350KB' #size of the file you want to upload
#In addition to these, also be sure to check the dependencies imported above.
#If you want to test the helao implementation of these functions, you must have a copy of the helao code
#To test the helao server requests, you must have kadi_server.py running
#To test the helao action requests, you must have kadi_server.py and kadi_action.py running


serverurl = 'http://127.0.0.1:13376'
actionurl = 'http://127.0.0.1:13377'
cname = yourname+'_test_'+unique
run = dict(token=KadiAPI.token,host=KadiAPI.host,unique=unique,username=yourname,runs=n,filepath=filepath,filename=filename,filesize=filesize,collection_name=cname)


if __name__ == "__main__":
    print('I am going to time a handful of Kadi functions in called in several different ways to thoroughly assess our runtime issues')
    print('first, calling the functions directly here')
    print('here, I will test record creation, modification of record attributes, linking records to a collection, uploading files to records, and record deletion')
    t0 = time.time()
    phase='direct'
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name,title=name,visibility='private',create=True)
            bar()
    direct_record_time = time.time() - t0
    run.update(dict(direct_record_time=direct_record_time))
    print(f'time to create {n} records: '+str(direct_record_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.set_attribute(attribute='title', value='modified_'+name)
            bar()
    direct_modify_time = time.time() - t0
    run.update(dict(direct_modify_time=direct_modify_time))
    print(f'time to modify {n} records: '+str(direct_modify_time))
    collection = Collection(identifier=cname,title=cname,create=True)
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.add_collection_link(Collection(identifier=cname).id)
            bar()
    direct_link_time = time.time() - t0
    run.update(dict(direct_link_time=direct_link_time))
    print(f'time to link {n} records: '+str(direct_link_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.upload_file(file_path=os.path.join(filepath,filename))
            bar()
    direct_upload_time = time.time() - t0
    run.update(dict(direct_upload_time=direct_upload_time))
    print(f'time to upload {n} files of size {filesize}:'+str(direct_upload_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.delete()
            bar()
    direct_delete_time = time.time() - t0
    run.update(dict(direct_delete_time=direct_delete_time))
    print(f'time to delete {n} records: '+str(direct_delete_time))
    print('well, that does it for the direct test. next I will work through our kadi_driver.py')
    print('I will call the functions addRecord, addRecordToCollection, addFileToRecord, recordExists, isFileInRecord, and downloadFilesFromRecord')
    print('I will have to delete these records natively')
    k = kadi(dict(host = r"https://polis-kadi4mat.iam-cms.kit.edu",PAT = r"52891e3a29fdf810abccc5ceda33b90a06e78ca25bcfac39",group='2'))
    phase = 'driver'
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            k.addRecord(name,name)
            bar()
    driver_addRecord_time = time.time() - t0
    run.update(dict(driver_addRecord_time=driver_addRecord_time))
    print(f'time to call addRecord {n} times: '+str(driver_addRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            k.addRecordToCollection(cname,name)
            bar()
    driver_addRecordToCollection_time = time.time() - t0
    run.update(dict(driver_addRecordToCollection_time=driver_addRecordToCollection_time))
    print(f'time to call addRecordToCollection {n} times: '+str(driver_addRecordToCollection_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            k.addFileToRecord(name,os.path.join(filepath,filename))
            bar()
    driver_addFileToRecord_time = time.time() - t0
    run.update(dict(driver_addFileToRecord_time=driver_addFileToRecord_time))
    print(f'time to call addFileToRecord {n} times: '+str(driver_addFileToRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            k.recordExists(name)
            bar()
    driver_recordExists_time = time.time() - t0
    run.update(dict(driver_recordExists_time=driver_recordExists_time))
    print(f'time to call recordExists {n} times: '+str(driver_recordExists_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            k.isFileInRecord(name,filename)
            bar()
    driver_isFileInRecord_time = time.time() - t0
    run.update(dict(driver_isFileInRecord_time=driver_isFileInRecord_time))
    print(f'time to call isFileInRecord {n} times: '+str(driver_isFileInRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            k.downloadFilesFromRecord(name,filepath)
            bar()
    driver_downloadFilesFromRecord_time = time.time() - t0
    run.update(dict(driver_downloadFilesFromRecord_time=driver_downloadFilesFromRecord_time))
    print(f'time to call downloadFilesFromRecord {n} times: '+str(driver_downloadFilesFromRecord_time))
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.delete()
            bar()
    print('now I am going to call the same functions as above, but by making requests to the kadi server')
    print('the server should now be online, so that this code does not crash')
    serverurl = 'http://127.0.0.1:13376'
    phase = 'server'
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/kadi/addrecord".format(serverurl), params={'ident':name,'title':name})
            bar()
    server_addRecord_time = time.time() - t0
    run.update(dict(server_addRecord_time=server_addRecord_time))
    print(f'time to call addRecord {n} times: '+str(server_addRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/kadi/addrecordtocollection".format(serverurl),params={'identCollection':cname,'identRecord':name})
            bar()
    server_addRecordToCollection_time = time.time() - t0
    run.update(dict(server_addRecordToCollection_time=server_addRecordToCollection_time))
    print(f'time to call addRecordToCollection {n} times: '+str(server_addRecordToCollection_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/kadi/addfiletorecord".format(serverurl),params={'identRecord':name,'filed':os.path.join(filepath,filename)})
            bar()
    server_addFileToRecord_time = time.time() - t0
    run.update(dict(server_addFileToRecord_time=server_addFileToRecord_time))
    print(f'time to call addFileToRecord {n} times: '+str(server_addFileToRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/kadi/recordexists".format(serverurl),params={'ident':name}).json()
            bar()
    server_recordExists_time = time.time() - t0
    run.update(dict(server_recordExists_time=server_recordExists_time))
    print(f'time to call recordExists {n} times: '+str(server_recordExists_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/kadi/isfileinrecord".format(serverurl),params={'ident':name,'filename':filename}).json()
            bar()
    server_isFileInRecord_time = time.time() - t0
    run.update(dict(server_isFileInRecord_time=server_isFileInRecord_time))
    print(f'time to call isFileInRecord {n} times: '+str(server_isFileInRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/kadi/downloadfilesfromrecord".format(serverurl),params={'ident':name,'filepath':filepath})
            bar()
    server_downloadFilesFromRecord_time = time.time() - t0
    run.update(dict(server_downloadFilesFromRecord_time=server_downloadFilesFromRecord_time))
    print(f'time to call downloadFilesFromRecord {n} times: '+str(server_downloadFilesFromRecord_time))
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.delete()
            bar()
    print('now I am going to test all the same functions a 3rd time, but through the action server')
    print('the action server had better now be on as well')
    actionurl = 'http://127.0.0.1:13377'
    phase = 'action'
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/data/addrecord".format(actionurl), params={'ident':name,'title':name})
            bar()
    action_addRecord_time = time.time() - t0
    run.update(dict(action_addRecord_time=action_addRecord_time))
    print(f'time to call addRecord {n} times: '+str(action_addRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/data/addrecordtocollection".format(actionurl),params={'identCollection':cname,'identRecord':name})
            bar()
    action_addRecordToCollection_time = time.time() - t0
    run.update(dict(action_addRecordToCollection_time=action_addRecordToCollection_time))
    print(f'time to call addRecordToCollection {n} times: '+str(action_addRecordToCollection_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/data/addfiletorecord".format(actionurl),params={'identRecord':name,'filed':os.path.join(filepath,filename)})
            bar()
    action_addFileToRecord_time = time.time() - t0
    run.update(dict(action_addFileToRecord_time=action_addFileToRecord_time))
    print(f'time to call addFileToRecord {n} times: '+str(action_addFileToRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/data/recordexists".format(actionurl),params={'ident':name}).json()
            bar()
    action_recordExists_time = time.time() - t0
    run.update(dict(action_recordExists_time=action_recordExists_time))
    print(f'time to call recordExists {n} times: '+str(action_recordExists_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/data/isfileinrecord".format(actionurl),params={'ident':name,'filename':filename}).json()
            bar()
    action_isFileInRecord_time = time.time() - t0
    run.update(dict(action_isFileInRecord_time=action_isFileInRecord_time))
    print(f'time to call isFileInRecord {n} times: '+str(action_isFileInRecord_time))
    t0 = time.time()
    with alive_bar(n) as bar:
        for i in range(n):
            name= yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            requests.get("{}/data/downloadfilesfromrecord".format(actionurl),params={'ident':name,'filepath':filepath})
            bar()
    action_downloadFilesFromRecord_time = time.time() - t0
    run.update(dict(action_downloadFilesFromRecord_time=action_downloadFilesFromRecord_time))
    print(f'time to call downloadFilesFromRecord {n} times: '+str(action_downloadFilesFromRecord_time))
    with alive_bar(n) as bar:
        for i in range(n):
            name = yourname+'_test_'+phase+'_'+unique+'_'+str(i)
            record = Record(identifier=name)
            record.delete()
            bar()
    with open(os.path.join(filepath,'_'+unique+'_output.json'),'w') as outfile:
        json.dump(run,outfile)