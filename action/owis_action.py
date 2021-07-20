import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import os
import time
import numpy
from importlib import import_module
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(helao_root)
from util import list_to_dict
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]


app = FastAPI(title="Owis action server V1",
    description="This is a very fancy Owis motor server",
    version="1.0")

class return_class(BaseModel):
    parameters: dict = None
    data: dict = None

@app.get("/owis/activate")
def activate(motor:int=0):
    res = requests.get("{}/owisDriver/activate".format(url),params={"motor":motor}).json()
    retc = return_class(parameters= {"motor": motor},data = res)
    return retc

@app.get("/owis/configure")
def configure(motor:int=0):
    res = requests.get("{}/owisDriver/configure".format(url),params={"motor":motor}).json()
    retc = return_class(measurement_type='owis',
                        parameters= {"motor": motor},
                        data = res)
    return retc


#move. units of loc are mm. if configured properly, valid inputs roughly between 0mm and 96mm (reading this on 15/04/21, I should qualify that we now have 1 motor which is longer than 96 mm)
#aiming to write this so that loc can be either a float (when there is only a single motor) or a list of floats
@app.get("/owis/move")
def move(loc,absol:bool=True):
    loc = json.loads(loc)
    if type(loc) == float or type(loc) == int:
        res = requests.get("{}/owisDriver/move".format(url),params={"count":int(loc*10000),"motor":0,"absol":absol}).json()
    else:
        res = []
        for i,j in zip(range(len(loc)),loc):
            res.append(requests.get("{}/owisDriver/move".format(url),params={"count":int(j*10000),"motor":i,"absol":absol}).json())
        res = list_to_dict(res)
    retc = return_class(parameters= {"loc": loc,"absol":absol,'units':{'loc':'mm'}},data = res)
    return retc

@app.get("/owis/getPos")
def getPos():
    res = requests.get("{}/owisDriver/getPos".format(url)).json()
    coordinates = res['data']['coordinates']
    loc = None if coordinates == None else coordinates/10000 if type(coordinates) == int else [i/10000 for i in coordinates]
    retc = return_class(parameters= None,data = {'res': {'loc':loc,'units':'mm'}, 'raw':res})
    return retc


@app.on_event("startup")
def memory():
    global height_map
    height_map = None

#3 coordinates which form a right triangle (or a rectangle with the origin included)
#coordinate x should be displaced only in x direction
#coordinate y should be displaced only in y direction
#coordinate m = (x[0],y[1],z) -- displaced in both directions
#third component of each coordinate is estimated sample height at that coordinate 'z'
def set_heights(x,m,y):
    global height_map
    height_map = lambda c: m[2]-(m[2]-x[2])/(m[1]-x[1])*(m[1]-c[1])-(m[2]-y[2])/(m[0]-y[0])*(m[0]-c[0])

#to keep coordinate system right-handed in current configuration, long motor should be x

#x,y,z,m set that is the motor position at which the center of the probe or whatever would be in contact with the sample stage origin
#m is the matrix by which to rotate/invert owis x-y to align it with sample stage x-y
#here we do the inverse of what one would expect, given that, and convert from sample stage coordinates to owis coordinates
def map_coordinates(c,key):
    d = config[serverkey]['coordinates'][config['owis']['roles'].index(key)]
    return numpy.append(numpy.dot(numpy.array(d[3]),numpy.array(c[:2])),c[2])+d[:3]

#believe me, I am not happy about this, but it does not seem prudent right now to continue thinking of a workaround
@app.get("/owis/calibration")
def calibration(x:str,m:str,y:str,d:float,minh:float=2,maxh:float=8,dh:float=.1,f:float=5,t:float=10,key:str='raman'):
    print("beginning action")
    ramanurl = config[serverkey]['ramanurl']
    z = config[serverkey]['coordinates'][config[serverkey]['roles'].index(key)][2]
    x0 = json.loads(x)
    m0 = json.loads(m)
    y0 = json.loads(y)
    xp = map_coordinates([x0[0],x0[1],0],key)[:2]
    mp = map_coordinates([m0[0],m0[1],0],key)[:2]
    yp = map_coordinates([y0[0],y0[1],0],key)[:2]
    xd = {config[serverkey]['roles'].index('x'):xp[0],config[serverkey]['roles'].index('y'):xp[1]}
    md = {config[serverkey]['roles'].index('x'):mp[0],config[serverkey]['roles'].index('y'):mp[1]}
    yd = {config[serverkey]['roles'].index('x'):yp[0],config[serverkey]['roles'].index('y'):yp[1]}
    res = []
    for i,j in xd.items():
        res.append(requests.get(f"{url}/owisDriver/move",params={"count":int(j*10000),"motor":i}).json())
    bestx = [None,0]
    for i in list(numpy.linspace(minh,maxh,int((maxh-minh)/dh)+1)):
        res.append(requests.get(f"{url}/owisDriver/move",params={"count":int((i+z+d)*10000),"motor":config[serverkey]['roles'].index(key)}).json())
        dat = requests.get(f"{ramanurl}/oceanDriver/readSpectrum",params={'t':1000000*t,'filename':"z_calibration_"+str(int(time.time()))+".json"}).json()
        inti = sum(dat['data']['intensities'])
        print([i,inti])
        if inti > bestx[1]:
            bestx = [i+d,inti]
        res.append(dat)
    for i,j in md.items():
        res.append(requests.get("{}/owisDriver/move".format(url),params={"count":int(j*10000),"motor":i}).json())
    bestm = [None,0]
    for i in list(numpy.linspace(minh,maxh,int((maxh-minh)/dh)+1)):
        res.append(requests.get("{}/owisDriver/move".format(url),params={"count":int((i+z+d)*10000),"motor":config[serverkey]['roles'].index(key)}).json())
        dat = requests.get(f"{ramanurl}/oceanDriver/readSpectrum",params={'t':1000000*t,'filename':"z_calibration_"+str(int(time.time()))+".json"}).json()
        inti = sum(dat['data']['intensities'])
        print([i,inti])
        if inti > bestm[1]:
            bestm = [i+d,inti]
        res.append(dat)
    for i,j in yd.items():
        res.append(requests.get("{}/owisDriver/move".format(url),params={"count":int(j*10000),"motor":i}).json())
    besty = [None,0]
    for i in list(numpy.linspace(minh,maxh,int((maxh-minh)/dh)+1)):
        res.append(requests.get("{}/owisDriver/move".format(url),params={"count":int((i+z+d)*10000),"motor":config[serverkey]['roles'].index(key)}).json())
        dat = requests.get(f"{ramanurl}/oceanDriver/readSpectrum",params={'t':1000000*t,'filename':"z_calibration_"+str(int(time.time()))+".json"}).json()
        inti = sum(dat['data']['intensities'])
        print([i,inti])
        if inti > besty[1]:
            besty = [i+d,inti]
        res.append(dat)
    #scipy.optimize.minimize_scalar(bracket=(1,f,2*f-1),bounds=(1,2*f-1),)
    set_heights(numpy.append(x0,bestx[0]-f),numpy.append(m0,bestm[0]-f),numpy.append(y0,besty[0]-f))
    return return_class(params = {'x':x,'m':m,'y':y,'d':d,'minh':minh,'maxh':maxh,'dh':dh,'f':f,'t':t,'key':key,'units':{'x':'mm','m':'mm','y':'mm','d':'mm','minh':'mm','maxh':'mm','dh':'mm','f':'mm','t':'s'}}, 
                        data = {'res':{'besthx':bestx,'besthm':bestm,'besthy':besty,'units':{'besthx':'mm','besthm':'mm','besthy':'mm'}},'raw':list_to_dict(res)})

#move table in x-y of sample stage coordinate system
@app.get("/owis/movetable")
def move_table(pos:str,key:str):
    #map x and y
    loc = json.loads(pos)
    loc = map_coordinates([loc[0],loc[1],0],key)[:2]
    loc = {config['owis']['roles'].index('x'):loc[0],config['owis']['roles'].index('y'):loc[1]}
    #move
    res = []
    for i,j in loc.items():
        res.append(requests.get(f"{url}/owisDriver/move",params={"count":int(j*10000),"motor":i}).json())
    retc = return_class(parameters= {"pos": pos,"key":key,'units':{'pos':'mm'}},data = list_to_dict(res))
    return retc

#move the given probe to a height z above sample stage
@app.get("/owis/moveprobe")
def move_probe(z:float,probe:str):
    d = config[serverkey]['coordinates'][config[serverkey]['roles'].index(probe)][2]
    res = requests.get("{}/owisDriver/move".format(url),params={"count":int((d+z+config[serverkey]['coordinates'][config[serverkey]['roles'].index(probe)][2])*10000),"motor":config[serverkey]['roles'].index(probe)}).json()
    retc = return_class(parameters= {"z": z,"probe":probe,'units':{'z':'mm'}},data = res)
    return retc

#same as above, but accounting for sample height profile
@app.get("/owis/sampleheight")
def sample_height(pos:str,f:float,probe:str):
    loc = json.loads(pos)
    d = config[serverkey]['coordinates'][config[serverkey]['roles'].index(probe)][2]
    z = f + height_map(loc)
    res = requests.get("{}/owisDriver/move".format(url),params={"count":int((d+z)*10000),"motor":config[serverkey]['roles'].index(probe)}).json()
    retc = return_class(parameters= {"pos": pos,"f":f,"probe":probe,'units':{'pos':'mm','f':'mm'}},data = res)
    return retc


if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                     port=config['servers'][serverkey]['port'])