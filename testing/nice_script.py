import sys
import os
import json
# I figure we will just use the driver so that you do not need to open any other windows
sys.path.append('C:/Users/jkflowers/Desktop/helao-dev/helao-dev/driver') #change this path to the one for your system. 
from kadi_driver import kadi
from sklearn.decomposition import NMF
import numpy


k = kadi(dict(host = r"https://polis-kadi4mat.iam-cms.kit.edu",
        PAT = r"52891e3a29fdf810abccc5ceda33b90a06e78ca25bcfac39",group='2'))

if __name__ == "__main__":
    downloadpath = 'C:/Users/jkflowers/Desktop/download_test' #change this path to an empty directory on your system
    k.downloadFilesFromCollection('stein_substrate_0',downloadpath) #this line times out for me, 
    #so nothing below here has been tested
    spectra = []
    grid = []
    for item in os.listdir(downloadpath):
        if item.split('_')[1] == 'raman':
            with open(os.path.join(downloadpath,item),'r') as infile:
                spectra.append(json.load(infile)['intensities'])
    with open(os.path.join(downloadpath,'spectra.json'),'w') as outfile:
        json.dump(spectra,outfile)
#this just pulls all the intensities out of spectra in downloaded collection and puts them into a filepath
#i would grab position too, but that is harder to reconstruct without having the orchestrator data

#now do machine learning i guess, just to have something to demonstrate
    X = numpy.transpose(numpy.asarray(spectra))
    model = NMF(n_components=3,init='random',solver='mu',beta_loss='kullback-leibler')
    W = model.fit_transform(X)
    H = model.components_
    with open(os.path.join(downloadpath,'H.json'),'w') as outfile:
        json.dump(numpy.transpose(H).tolist(),outfile) #weights
    with open(os.path.join(downloadpath,'W.json'),'w') as outfile:
        json.dump(numpy.transpose(W).tolist(),outfile) #basis vectors