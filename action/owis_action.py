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
def activate(motor: int = 0):
    res = requests.get("{}/owisDriver/activate".format(url),
                       params={"motor": motor}).json()
    retc = return_class(parameters={"motor": motor}, data=res)
    return retc

@app.get("/owis/configure")
def configure(motor: int = 0):
    res = requests.get("{}/owisDriver/configure".format(url),
                       params={"motor": motor}).json()
    retc = return_class(measurement_type='owis',
                        parameters={"motor": motor},
                        data=res)
    return retc

# move. units of loc are mm. if configured properly, valid inputs roughly between 0mm and 96mm (reading this on 15/04/21, I should qualify that we now have 1 motor which is longer than 96 mm)
# aiming to write this so that loc can be either a float (when there is only a single motor) or a list of floats
def mov(loc, absol: bool = True):
    if type(loc) == float or type(loc) == int:
        res = requests.get("{}/owisDriver/move".format(url),
                           params={"count": int(loc*10000), "motor": 0, "absol": absol}).json()
    else:
        res = []
        for i, j in zip(range(len(loc)), loc):
            if j != None:
                res.append(requests.get("{}/owisDriver/move".format(url),params={"count": int(j*10000), "motor": i, "absol": absol}).json())
        res = list_to_dict(res)
    return res

@app.get("/owis/move")
def move(loc, absol: bool = True):
    loc = json.loads(loc)
    res = mov(loc,absol)
    retc = return_class(parameters={"loc": loc, "absol": absol, 'units': {'loc': 'mm'}}, data=res)
    return retc

def getP():
    res = requests.get("{}/owisDriver/getPos".format(url)).json()
    coordinates = res['data']['coordinates']
    loc = None if coordinates == None else coordinates / 10000 if type(coordinates) == int else [i/10000 for i in coordinates]
    return loc,res

@app.get("/owis/getPos")
def getPos():
    loc,res = getP()
    retc = return_class(parameters=None, data={
                        'res': {'loc': loc, 'units': 'mm'}, 'raw': res})
    return retc

@app.get("/owis/setCurrent")
def setCurrent(dri:int,hol:int,amp:int,motor:int=0):
    res = requests.get("{}/owisDriver/setCurrent".format(url),params={"dri":dri,"hol":hol,"amp":amp,"motor":motor}).json()
    retc = return_class(parameters={"dri":dri,"hol":hol,"amp":amp,"motor":motor},data=res)
    return retc

#convert sample x-y to motor x-y
#so you take a sample x-y, convert that to the reference coordinate system on the sample
#that coordinate system is already lined up with the motor coordinate system,
# but has it's origin at the point where the probe is in contact with the reference point, and needs to be translated accordingly
def map_coordinates(c:numpy.array,probe:str,sample:str):
    coordinates = config[serverkey]['coordinates'][sample]
    cs, sn = numpy.cos(coordinates['theta']), numpy.sin(coordinates['theta'])
    I = numpy.array([[1,0],[0,1]]) if coordinates['I'] else numpy.array([[-1,0],[0,1]])
    #v1 = IR(-theta)v2 + [x,y]
    return I.dot(numpy.array([[cs,sn],[-sn,cs]])).dot(c) + numpy.array([coordinates['x'],coordinates['y']]) + config[serverkey]['probes'][probe]['coordinates'][:2]

#convert motor x-y to sample x-y
def reverse_coordinates(c:numpy.array,probe:str,sample:str):
    coordinates = config[serverkey]['coordinates'][sample]
    cs, sn = numpy.cos(coordinates['theta']), numpy.sin(coordinates['theta'])
    I = numpy.array([[1,0],[0,1]]) if coordinates['I'] else numpy.array([[-1,0],[0,1]])
    #v2 = R(theta)I(v1-[x,y])
    return numpy.array([[cs,-sn],[sn,cs]]).dot(I).dot(c-numpy.array([coordinates['x'],coordinates['y']])-config[serverkey]['probes'][probe]['coordinates'][:2])

# move table in x-y of sample stage coordinate system
#  if surface, go to the appropriate measuring height as defined by surface
@app.get("/owis/movetable")
def move_table(pos: str, probe: str, sample: str, surf:bool = False):
    global surface
    # map x and y
    start,locres = getP()
    startc = reverse_coordinates(numpy.array([start[config[serverkey]['x']],start[config[serverkey]['y']]]),probe,sample)
    loc = json.loads(pos)
    loc = [loc[i] if loc[i] != None else startc[i] for i in range(len(loc))]
    loc = map_coordinates(loc, probe, sample)
    # move
    res = mov([loc[0] if i == config[serverkey]["x"] else loc[1] if i == config[serverkey]["y"] else None for i in range(config[serverkey]["n"])])
    retc = return_class(parameters={"pos": pos, "probe": probe, "sample": sample, 'units': {'pos': 'mm'}}, data={0:res,1:locres})
    return retc

# move the given probe to a height z above sample stage, or, optionally, height z above a surface
@app.get("/owis/moveprobe")
def move_probe(z: float, probe: str, sample: str, surf: bool = False):
    global surface
    d = config[serverkey]["probes"][probe]["coordinates"][2]+config[serverkey]["coordinates"][sample]["z"]
    if surf:
        loc,res2 = getP()
        s = surface(loc[0],loc[1])
        count = int((d+z+s)*10000)
    else:
        count = int((d+z)*10000)
    res = requests.get("{}/owisDriver/move".format(url), params={"count": count, "motor": config[serverkey]["probes"][probe]["motor"]}).json()
    if surf:
        res = {'0':res2,'1':res}
    retc = return_class(parameters={"z": z, "probe": probe, 'surface': surface, 'units': {'z': 'mm'}}, data=res)
    return retc

#maybe i should put in a "measure", function, that calls move table and then puts you at the focal distances, optional thickness mod.

#move the given probe to the given reference point
@app.get("/owis/goref")
def goto_ref(probe: str, ref: str):
    coord = numpy.array(config[serverkey]['references'][ref])+numpy.array(config[serverkey]['probes'][probe]['coordinates'])+numpy.array([0,0,config[serverkey]['probes'][probe]['focal']])
    loc = [coord[0] if i == config[serverkey]["x"] else coord[1] if i == config[serverkey]["y"] else coord[2] if i == config[serverkey]["probes"][probe]["motor"] else None for i in range(config[serverkey]["n"])]
    print(loc)
    res = mov(loc)
    retc = return_class(parameters={"probe": probe, "ref": ref}, data=res)
    return retc

#submit a list of 3 positions in the given coordinate system to define a surface
# surface will be saved in motor coordinate system and translated into other coordinate systems as needed.
# basically this is just the math to find a plane from 3 points
@app.get("/owis/surface")
def define_surface(p1:str,p2:str,p3:str,probe: str, sample: str):
    global surface
    v1,v2,v3 = numpy.array(json.loads(p1)),numpy.array(json.loads(p2)),numpy.array(json.loads(p3))
    p = numpy.cross(v3-v1,v2-v1)
    a,b,c,d = p,numpy.dot(p,p1)
    surface = lambda x,y: (d-a*x-b*y)/c - config[serverkey]['focals'][probe] # compensating for focal length of the probe used for surface.
    retc = return_class(parameters={'p1':p1,'p2':p2,'p3':p3,'probe':probe,'sample':sample,'units':{'p1':'mm','p2':'mm','p3':'mm'}}, 
                        data={'plane':{'a':a,'b':b,'c':c,'d':d,'units':{'a':'mm','b':'mm','c':'mm','d':'mm'}}})
    return retc

#reset surface to default
@app.get("/owis/clearsurface")
def clear_surface():
    global surface
    surface = lambda x,y: 0
    retc = return_class(parameters=None, data=None)
    return retc

@app.on_event("startup")
def memory():
    global surface
    surface = lambda x,y: 0

#putting the z stuff on hold for a bit until we can figure out what is going on.
'''
@app.on_event("startup")
def memory():
    global height_map
    height_map = None

# 3 coordinates which form a right triangle (or a rectangle with the origin included)
# coordinate x should be displaced only in x direction
# coordinate y should be displaced only in y direction
# coordinate m = (x[0],y[1],z) -- displaced in both directions
# third component of each coordinate is estimated sample height at that coordinate 'z'


def set_heights(x, m, y):
    global height_map
    def height_map(c): return m[2]-(m[2]-x[2])/(m[1]-x[1]) * \
        (m[1]-c[1])-(m[2]-y[2])/(m[0]-y[0])*(m[0]-c[0])

# to keep coordinate system right-handed in current configuration, long motor should be x

# x,y,z,m set that is the motor position at which the center of the probe or whatever would be in contact with the sample stage origin
# m is the matrix by which to rotate/invert owis x-y to align it with sample stage x-y
# here we do the inverse of what one would expect, given that, and convert from sample stage coordinates to owis coordinates


def map_coordinates(c, key):
    d = config[serverkey]['coordinates'][config['owis']['roles'].index(key)]
    return numpy.append(numpy.dot(numpy.array(d[3]), numpy.array(c[:2])), c[2])+d[:3]

# believe me, I am not happy about this, but it does not seem prudent right now to continue thinking of a workaround


@app.get("/owis/calibration")
def calibration(x: str, m: str, y: str, d: float, minh: float = 2, maxh: float = 8, dh: float = .1, f: float = 5, t: float = 10, key: str = 'raman'):
    print("beginning action")
    ramanurl = config[serverkey]['ramanurl']
    z = config[serverkey]['coordinates'][config[serverkey]
                                         ['roles'].index(key)][2]
    x0 = json.loads(x)
    m0 = json.loads(m)
    y0 = json.loads(y)
    xp = map_coordinates([x0[0], x0[1], 0], key)[:2]
    mp = map_coordinates([m0[0], m0[1], 0], key)[:2]
    yp = map_coordinates([y0[0], y0[1], 0], key)[:2]
    xd = {config[serverkey]['roles'].index(
        'x'): xp[0], config[serverkey]['roles'].index('y'): xp[1]}
    md = {config[serverkey]['roles'].index(
        'x'): mp[0], config[serverkey]['roles'].index('y'): mp[1]}
    yd = {config[serverkey]['roles'].index(
        'x'): yp[0], config[serverkey]['roles'].index('y'): yp[1]}
    res = []
    for i, j in xd.items():
        res.append(requests.get(
            f"{url}/owisDriver/move", params={"count": int(j*10000), "motor": i}).json())
    bestx = [None, 0]
    for i in list(numpy.linspace(minh, maxh, int((maxh-minh)/dh)+1)):
        res.append(requests.get(f"{url}/owisDriver/move", params={"count": int(
            (i+z+d)*10000), "motor": config[serverkey]['roles'].index(key)}).json())
        dat = requests.get(f"{ramanurl}/oceanDriver/readSpectrum", params={
                           't': 1000000*t, 'filename': "z_calibration_"+str(int(time.time()))+".json"}).json()
        inti = sum(dat['data']['intensities'])
        print([i, inti])
        if inti > bestx[1]:
            bestx = [i+d, inti]
        res.append(dat)
    for i, j in md.items():
        res.append(requests.get("{}/owisDriver/move".format(url),
                                params={"count": int(j*10000), "motor": i}).json())
    bestm = [None, 0]
    for i in list(numpy.linspace(minh, maxh, int((maxh-minh)/dh)+1)):
        res.append(requests.get("{}/owisDriver/move".format(url), params={"count": int(
            (i+z+d)*10000), "motor": config[serverkey]['roles'].index(key)}).json())
        dat = requests.get(f"{ramanurl}/oceanDriver/readSpectrum", params={
                           't': 1000000*t, 'filename': "z_calibration_"+str(int(time.time()))+".json"}).json()
        inti = sum(dat['data']['intensities'])
        print([i, inti])
        if inti > bestm[1]:
            bestm = [i+d, inti]
        res.append(dat)
    for i, j in yd.items():
        res.append(requests.get("{}/owisDriver/move".format(url),
                                params={"count": int(j*10000), "motor": i}).json())
    besty = [None, 0]
    for i in list(numpy.linspace(minh, maxh, int((maxh-minh)/dh)+1)):
        res.append(requests.get("{}/owisDriver/move".format(url), params={"count": int(
            (i+z+d)*10000), "motor": config[serverkey]['roles'].index(key)}).json())
        dat = requests.get(f"{ramanurl}/oceanDriver/readSpectrum", params={
                           't': 1000000*t, 'filename': "z_calibration_"+str(int(time.time()))+".json"}).json()
        inti = sum(dat['data']['intensities'])
        print([i, inti])
        if inti > besty[1]:
            besty = [i+d, inti]
        res.append(dat)
    # scipy.optimize.minimize_scalar(bracket=(1,f,2*f-1),bounds=(1,2*f-1),)
    set_heights(numpy.append(
        x0, bestx[0]-f), numpy.append(m0, bestm[0]-f), numpy.append(y0, besty[0]-f))
    return return_class(params={'x': x, 'm': m, 'y': y, 'd': d, 'minh': minh, 'maxh': maxh, 'dh': dh, 'f': f, 't': t, 'key': key, 'units': {'x': 'mm', 'm': 'mm', 'y': 'mm', 'd': 'mm', 'minh': 'mm', 'maxh': 'mm', 'dh': 'mm', 'f': 'mm', 't': 's'}},
                        data={'res': {'besthx': bestx, 'besthm': bestm, 'besthy': besty, 'units': {'besthx': 'mm', 'besthm': 'mm', 'besthy': 'mm'}}, 'raw': list_to_dict(res)})

# same as above, but accounting for sample height profile
@app.get("/owis/sampleheight")
def sample_height(pos: str, f: float, probe: str):
    loc = json.loads(pos)
    d = config[serverkey]['coordinates'][config[serverkey]
                                         ['roles'].index(probe)][2]
    z = f + height_map(loc)
    res = requests.get("{}/owisDriver/move".format(url), params={"count": int(
        (d+z)*10000), "motor": config[serverkey]['roles'].index(probe)}).json()
    retc = return_class(parameters={"pos": pos, "f": f, "probe": probe, 'units': {
                        'pos': 'mm', 'f': 'mm'}}, data=res)
    return retc
'''


if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'],
                port=config['servers'][serverkey]['port'])
