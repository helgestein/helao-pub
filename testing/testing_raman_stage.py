import sys
sys.path.append("../action")
sys.path.append("../config")
sys.path.append("../orchestrators")
from mischbares_small import config
import movement_mecademic as mm
import owis_action as oa
import raman_ocean as ro
import time
import mischbares
import json
from fastapi import FastAPI,BackgroundTasks
import requests
import numpy
from sklearn.decomposition import NMF

#check if home, check if stage is aligned, check optimal probe height, for each sample:[move sample into position, move probe to optimal measuring point, measure, move probe to home
#0,80 is where we are at now for the origin i think?
x, y = numpy.meshgrid([2.5 * i for i in range(27)], [2.5 * i for i in range(8)])
x, y = x.flatten(), y.flatten()
grid = [[x[i]+5,y[i]+10] for i in range(len(x))]

#motor 0 count increases as y increases
#motor 1 count increases as x decreases

grid = [[46.6+i[1],79.4-i[0]] for i in grid]



if __name__ == "__main__":
    print(str(grid))
    task = "map"
    h = 1
    t = 10000000
    zs = json.dumps([i/5 for i in range(10,41)])
    x1 = [74.1,74.4]
    x2 = [74.1,9.4]
    x3 = [56.6,9.4]
    mm.url = "http://{}:{}".format(config['servers']['mecademicServer']['host'], config['servers']['mecademicServer']['port'])
    oa.url = "http://{}:{}".format(config['servers']['owisServer']['host'], config['servers']['owisServer']['port'])
    ro.url = "http://{}:{}".format(config['servers']['oceanServer']['host'], config['servers']['oceanServer']['port'])
    safepath = "C:/Users/Operator/Documents/temp"
    if task == "test":
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        oa.move(json.dumps(x1))
        z1 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x2))
        z2 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x3))
        z3 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
        mm.safe_raman()
        print([z1,z2,z3])
        for loc in grid:
            oa.move(json.dumps(loc))
            mm.measuring_raman(z(loc),h)
            ro.read(t,"C:/Users/Operator/Documents/temp/test_raman_"+time.time())
            mm.safe_raman()
    if task == "make":
        soe = []
        params = {}
        soe.append("movement/moveToHome_0")
        params.update({"moveToHome_0":None})
        soe.append("table/configure_0")
        params.update({"configure_0":dict(motor=0)})
        soe.append("table/configure_1")
        params.update({"configure_1":dict(motor=1)})
        i = 0
        for loc in grid:
            soe.append("table/move_{}".format(i))
            params.update({"move_{}".format(i):dict(loc=json.dumps(loc))})
            soe.append("movement/measuringRaman_{}".format(i))
            params.update({"measuringRaman_{}".format(i):dict(z=5,h=1)})
            soe.append("oceanAction/read_{}".format(i))
            params.update({"read_{}".format(i):dict(t=10000000,filename="C:/Users/Operator/Documents/temp/dry_dry_"+str(i))})
            soe.append("movement/safeRaman_{}".format(i+1))
            params.update({"safeRaman_{}".format(i+1):None})
            i += 1
        experiment = dict(soe=soe,params=params,meta=dict(substrate="coppertape1",ma="lmao"))
        #experiment = dict(soe=["movement/moveToHome_0"],params=dict(moveToHome_0=None),meta=dict(substrate="dry",ma="dry"))
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"addExperiment"),params= dict(experiment=json.dumps(experiment)))
        requests.post("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'] ,13380 ,"orchestrator" ,"infiniteLoop"),params= None)
    if task == "calibrate":
        oa.move(json.dumps(x1))
        z1 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x2))
        z2 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x3))
        z3 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
        mm.safe_raman()
        print([z1,z2,z3])
    if task == "test_calibration":
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        oa.move(json.dumps(x1))
        z1 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x2))
        z2 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x3))
        z3 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
        mm.safe_raman()
        print([z1,z2,z3])
        for loc in grid:
            oa.move(json.dumps(loc))
            zc = mm.calibrate_raman(h,t,safepath).data['best']['z']
            print({'zc':zc,'z':z(loc)})
            mm.safe_raman()
    if task == "map":
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        oa.move(json.dumps(x1))
        z1 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x2))
        z2 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(x3))
        z3 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
        mm.safe_raman()
        print([z1,z2,z3])
        X = []
        grid = [[i/10,j/10] for i in range(566,746,5) for j in range(744,89,-5)]
        for loc in grid:
            oa.move(json.dumps(loc))
            print([loc,z(loc)])
            mm.measuring_raman(z(loc),h)
            X.append(ro.read(t,"C:/Users/Operator/Documents/temp/test_raman_"+str(time.time())).data['data']['intensities'])
            mm.safe_raman()
        X = numpy.transpose(numpy.asarray(X))
        json.dump([[grid[i], X[i]] for i in range(len(grid))],"C:/Users/Operator/Desktop/Xgrid.json")
        model = NMF(n_components=3,init='random',solver='mu',beta_loss='kullback-leibler')
        W = model.fit_transform(X)
        H = model.components_
        columns = numpy.transpose(H)
        output = [[grid[i], columns[i]] for i in range(len(grid))]
        json.dump(output,"C:/Users/Operator/Desktop/Hgrid.json")


