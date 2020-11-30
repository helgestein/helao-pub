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
    task = "test_calibration2"
    h = 2
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
            ro.read(t,"C:/Users/Operator/Documents/temp/test_raman_"+time.time().replace('.','_'))
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
        x1,x2,x3 = [35,10],[35,40],[5,40]
        grid = [[i,j] for i in range(5,36) for j in range(10,41)]
        conv = lambda x: [46.6+x[1],79.4-x[0]]
        grid = map(conv,grid)
        zs = json.dumps([i/10 for i in range(20,41)])
        oa.move(json.dumps(conv(x1)))
        z1 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(conv(x2)))
        z2 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        oa.move(json.dumps(conv(x3)))
        z3 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
        z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
        mm.safe_raman()
        print([z1,z2,z3])
        data = [[z1,z2,z3]]
        for loc in grid:
            oa.move(json.dumps(loc))
            zc = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
            print({'zc':zc,'z':z(loc)})
            data.append([loc,{'zc':zc,'z':z(loc)}])
            mm.safe_raman()
        with open(r"C:\Users\Operator\Desktop\Zcal.json",'w') as outfile:
            json.dump(data,outfile)
    if task == "map":
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        z1,z2,z3 = 5.4,5.0,5.4
        z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
        mm.safe_raman()
        print([z1,z2,z3])
        X = []
        grid = [[i/10,j/10] for i in range(650,701) for j in range(600,701)]
        for loc in grid:
            oa.move(json.dumps(loc))
            print([loc,z(loc)])
            mm.measuring_raman(z(loc),h)
            X.append(ro.read(t,"C:/Users/Operator/Documents/temp/test_raman_"+str(time.time()).replace('.','_')).data['data']['intensities'])
            mm.safe_raman()
        with open(r"C:\Users\Operator\Desktop\Xgridmini.json",'w') as outfile:
            json.dump([[grid[i], X[i]] for i in range(len(grid))],outfile)
        X = numpy.transpose(numpy.asarray(X))
        model = NMF(n_components=3,init='random',solver='mu',beta_loss='kullback-leibler')
        W = model.fit_transform(X)
        H = model.components_
        columns = numpy.transpose(H)
        output = [[grid[i], columns[i].tolist()] for i in range(len(grid))]
        with open(r"C:\Users\Operator\Desktop\Hgridmini.json",'w') as outfile:
            json.dump(output,outfile)
        with open(r"C:\Users\Operator\Desktop\Wgridmini.json",'w') as outfile:
            json.dump(W.tolist(),outfile)
    if task == "test_calibration2":
        mm.move_to_home()
        oa.configure(0)
        oa.configure(1)
        x1,x2,x3 = [35,10],[35,40],[5,40]
        grid = [[i,j] for i in range(5,36) for j in range(10,41)]
        conv = lambda x: [46.6+x[1],79.4-x[0]]
        grid = map(conv,grid)
        hs = [2,2.1,2.2,2.3,2.4,2.5,2.6,2.7,2.8,2.9,3,3.1,3.2,3.3,3.4,3.5,3.6,3.7,3.8,3.9,4,4.1,4.2,4.3,4.4,4.5,4.6,4.7,4.8,4.9,5]
        for h in hs:
            zs = json.dumps([i/10 for i in range(20,81)])
            oa.move(json.dumps(conv(x1)))
            z1 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
            oa.move(json.dumps(conv(x2)))
            z2 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
            oa.move(json.dumps(conv(x3)))
            z3 = mm.calibrate_raman(zs,h,t,safepath).data['best']['z']
            z = lambda x: z2-(z2-z1)/(x2[1]-x1[1])*(x2[1]-x[1])-(z2-z3)/(x2[0]-x3[0])*(x2[0]-x[0])
            mm.safe_raman()
            print({'h':h,'zs':[z1,z2,z3]})

