import sys
sys.path.append(r"../")
import json
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
#from celery import group
#import hdfdict
import os
import requests
import h5py
from importlib import import_module
from random import uniform
import numpy as np
from scipy.integrate import simpson
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(helao_root)
sys.path.append(os.path.join(helao_root, 'config'))
config = import_module(sys.argv[1]).config
from util import highestName, dict_address, hdf5_group_to_dict
serverkey = sys.argv[2]
from contextlib import asynccontextmanager

import scipy.stats as st
import impedance.models.circuits as circuits
from impedance.validation import linKK
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('agg')

app = FastAPI(title="Analysis V2",
              description="This is a fancy analysis server",
              version="2.0")

class return_class(BaseModel):
    parameters :dict = None
    data: dict = None

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    global data
    data = []
    yield

@app.get("/analysis/receiveData")
def receiveData(path: str, run: int, address: str):
    global data
    data = [] # i don't need to load the data from pervious exp
    try:
        address = json.loads(address)
    except:
        address = [address]
    newdata = []
    print(address)
    for add in address:
        with h5py.File(path, 'r') as h5file:
            add = f'run_{run}/'+add+'/'
            print(add)
            if isinstance(h5file[add],h5py.Group):
                newdata.append(hdf5_group_to_dict(h5file, add))
            else:
                newdata.append(h5file[add][()])
    print(f"data is {newdata}")
    data.append(newdata[0] if len(newdata) == 1 else newdata)
    print(f'Data is {data}')

@app.get("/analysis/dummy")
def bridge(address:str):
    global data
    x = data[0][0]
    y = data[0][1]
    z = data[0][2]
    #print("data", data)
    #print("addresses", addresses)
    retc = return_class(parameters={'addresses':address}, data={'x':{'x':x,'y':y},'y':{'z':z}})
    return retc

@app.get("/analysis/ocp")
def ocp(address:str):
    global data
    ocp0 = data[0][0][:-4][-10:]
    ocp1 = data[0][1][:-4][-10:]
    ocp2 = data[0][2][:-4][-10:]
    ocp3 = data[0][3][:-4][-10:]
    ocp0_res, ocp0_err = np.mean(ocp0), 2*np.std(ocp0)
    ocp1_res, ocp1_err = np.mean(ocp1), 2*np.std(ocp1)
    ocp2_res, ocp2_err = np.mean(ocp2), 2*np.std(ocp2)
    ocp3_res, ocp3_err = np.mean(ocp3), 2*np.std(ocp3)
    retc = return_class(parameters={'addresses':address}, data={'res':{'OCP0': ocp0_res, 'OCP1': ocp1_res, 'OCP2': ocp2_res, 'OCP3': ocp3_res},
                                                                'err':{'OCP0': ocp0_err, 'OCP1': ocp1_err, 'OCP2': ocp2_err, 'OCP3': ocp3_err}})
    return retc

@app.get("/analysis/eis0")
def eis_short(run: int, address: str):
    global data
    print(data)
    ReZ_ = data[0][0]
    ImZ_ = data[0][1]
    freq_ = data[0][2]
    ReZ_ids = np.where(ReZ_ > 0)[0]
    ImZ_ids = np.where(ImZ_ > 0)[0]
    ids = [i for i in ImZ_ids if i in ReZ_ids]
    ReZ = ReZ_[ids]
    ImZ = ImZ_[ids]
    freq = freq_[ids]
    Z = np.array(ReZ)-np.array(ImZ)*1j
    angle = np.arctan(ImZ/ReZ)*90
    
    def local_minimum(data, threshold, window_size):
        filtered_data = [x if x < threshold else np.nan for x in data] # Filter out values above the threshold
        smoothed_data = np.convolve(data, np.ones(window_size), 'valid') / window_size # Smooth the data
        minimum_indices = [] # Find the local minimum indices
        for i in range(1, len(smoothed_data) - 1):
            if not np.isnan(smoothed_data[i]) and smoothed_data[i-1] > smoothed_data[i] < smoothed_data[i+1]:
                minimum_indices.append(i + window_size // 2)  # Adjust index for window size
                if len(minimum_indices) == 2:
                    break
        while len(minimum_indices) < 2: # Ensure the list has two elements, using None as a placeholder if necessary
            minimum_indices.append(None)
        return minimum_indices

    threshold = 90
    window_size = 5

    ids_min = local_minimum(angle, threshold, window_size)
    id0 = next((index for index, value in enumerate(angle) if value > 0), 0)
    R0_guess = 0.95*ReZ[id0]
    R0_min = 0.5*R0_guess
    R0_max = 1.05*R0_guess

    if ids_min[0] == None:
        R1_guess = 1000
        R1_min = 0
        R1_max = 100000
    else:
        R1_guess = abs(ReZ[ids_min[0]] - R0_guess)
        R1_min = abs(0.5*R1_guess)
        R1_max = abs(1.5*R1_guess)

    if ids_min[1] == None:
        circuit_0='R_0-p(R_1,CPE_1)-CPE_2'
        initial_guess_0=[R0_guess, R1_guess, 1e-10, 0.99, 1e-7, 0.8]
        bounds_0 = (R0_min, R1_min, 1e-13, 0.001, 1e-13, 0),(R0_max, R1_max, 1e-5, 0.999, 1e-3, 1)
        R2_guess = 1.5*R1_guess
        R2_min = 0.5*R2_guess
        R2_max = 3*R2_guess
        circuit_1='R_0-p(R_1,CPE_1)-p(R_2,CPE_2)-CPE_3'
        initial_guess_1=[R0_guess, R1_guess, 1e-11,0.98, R2_guess, 4e-7,0.85, 1e-6,0.9]
        bounds_1 = (R0_min, R1_min, 1e-13,0.001, 0, 1e-13,0.001, 1e-13,0.001),(R0_max, R1_max, 1e-8,1, 100000, 1e-4,1, 1,1)
        if len(ReZ)<4:
            R0, R1, CPE1_Y, CPE1_n, CPE2_Y, CPE2_n = ReZ[0], None, None, None, None, None
            R0_err, R1_err, CPE1_Y_err, CPE1_n_err, CPE2_Y_err, CPE2_n_err = None, None, None, None, None, None
            chi2, chi2_KK = None, None
            retc = return_class(parameters={'addresses':address}, data={'res':{'R0': R0}})
        else:
            res_fit_0, uns_fit_0 = circuits.fitting.circuit_fit(freq, Z, circuit=circuit_0, initial_guess=initial_guess_0, constants={}, bounds=bounds_0, weight_by_modulus=True, global_opt=False)
            res_fit_1, uns_fit_1 = circuits.fitting.circuit_fit(freq, Z, circuit=circuit_1, initial_guess=initial_guess_1, constants={}, bounds=bounds_1, weight_by_modulus=True, global_opt=False)
            circuit_test_0 = circuits.CustomCircuit(circuit=circuit_0, initial_guess=res_fit_0)
            circuit_test_1 = circuits.CustomCircuit(circuit=circuit_1, initial_guess=res_fit_1)
            ### chi2
            Z_fit_0 = circuit_test_0.predict(freq)
            Z_fit_1 = circuit_test_1.predict(freq)
            chi2_0 = np.sum((Z_fit_0.real - Z.real)**2/(Z.real**2+Z.imag**2))+np.sum((Z_fit_0.imag - Z.imag)**2/(Z.real**2+Z.imag**2))
            chi2_1 = np.sum((Z_fit_1.real - Z.real)**2/(Z.real**2+Z.imag**2))+np.sum((Z_fit_1.imag - Z.imag)**2/(Z.real**2+Z.imag**2))
            M, mu, Z_linKK, res_real, res_imag = linKK(freq, Z, c=0.85, max_M=1000, fit_type='complex', add_cap=True)
            chi2_KK = np.sum((res_real)**2) + np.sum((res_imag)**2)
            ### decision
            res_fit = res_fit_0 if chi2_0 < 0.75*chi2_1 else res_fit_1
            R0, R1, CPE1_Y, CPE1_n, R2, CPE2_Y, CPE2_n, CPE3_Y, CPE3_n = (res_fit[0], res_fit[1], res_fit[2], None, res_fit[3], res_fit[4], res_fit[5], None, None) if chi2_0 < 0.75*chi2_1 else (res_fit[0], res_fit[1], res_fit[2], res_fit[3], res_fit[4], res_fit[5], res_fit[6], res_fit[7], res_fit[8])
            uns_fit = uns_fit_0 if chi2_0 < 0.75*chi2_1 else uns_fit_1
            Z_fit = Z_fit_0 if chi2_0 < 0.75*chi2_1 else Z_fit_1
            chi2 = chi2_0 if chi2_0 < 0.75*chi2_1 else chi2_1
            if isinstance(uns_fit, type(None)):
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, CPE3_Y_err, CPE3_n_err = None, None, None, None, None, None, None, None, None
            else:
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, CPE3_Y_err, CPE3_n_err = (uns_fit[0], uns_fit[1], uns_fit[2], uns_fit[3], None, uns_fit[4], uns_fit[5], None, None) if chi2_0 < 0.75*chi2_1 else (uns_fit[0], uns_fit[1], uns_fit[2], uns_fit[3], uns_fit[4], uns_fit[5], uns_fit[6], uns_fit[7], uns_fit[8])
            # plot
            plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
            plt.rcParams["axes.labelweight"] = "bold" # general thing
            fig, ax = plt.subplots(figsize=(9,6),dpi=100)
            scatter = ax.scatter(Z.real/1e3, -Z.imag/1e3, facecolors='none', edgecolors='b', linewidth = 1, s = 15, label = 'Data')
            line, = ax.plot(Z_fit.real/1e3, -Z_fit.imag/1e3, color='r', alpha = 1.00, linewidth = 1.5, label = 'Fit')
            max_ = 1.05*max(max(Z.real/1e3), max(-Z.imag/1e3))
            ax.set_xlim(xmin=0, xmax=max_)
            ax.set_ylim(ymin=0, ymax=max_)
            ax.set_aspect('equal', adjustable='box')
            tick_interval = np.round(max_ / 5, -int(np.floor(np.log10(max_ / 5))))
            tick_values = np.arange(0, max_ + tick_interval, tick_interval)
            ax.set_xticks(tick_values)
            ax.set_yticks(tick_values) 
            ax.tick_params(which='both', labelsize=16, width=1.5)
            ax.set_xlabel("Z', kΩ", fontsize=20)
            ax.set_ylabel("-Z'', kΩ", fontsize=20)
            handles = [scatter, line, plt.Line2D([], [], color='none')]
            labels = ['Data', 'Fit', f'χ²: {chi2:.4f}']
            ax.legend(handles, labels, title=f"Run {int(run/4)}, cycle {int(run%4)}", title_fontsize='medium', prop={'size': 'medium'})
            plt.savefig( f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/EIS/eis_{int(run/4)}_{int(run%4)}.png", transparent=False)
            plt.clf()
            plt.close('all')
            #return
            if chi2_0 < 0.75*chi2_1:
                retc = return_class(parameters={'addresses':address}, data={'res':{'R0': R0, 'R1': R1, 'CPE1_Y': CPE1_Y, 'CPE1_n': CPE1_n, 'CPE2_Y': CPE2_Y, 'CPE2_n': CPE2_n},
                                                                'err':{'R0': R0_err, 'R1': R1_err, 'CPE1_Y': CPE1_Y_err, 'CPE1_n': CPE1_n_err, 'CPE2_Y': CPE2_Y_err, 'CPE2_n': CPE2_n_err},
                                                                'chi2':{'fit': chi2, 'KK':chi2_KK}})
            else:
                retc = return_class(parameters={'addresses':address}, data={'res':{'R0': R0, 'R1': R1, 'CPE1_Y': CPE1_Y, 'CPE1_n': CPE1_n, 'R2': R2, 'CPE2_Y': CPE2_Y, 'CPE2_n': CPE2_n, 'CPE3_Y': CPE3_Y, 'CPE3_n': CPE3_n},
                                                                    'err':{'R0': R0_err, 'R1': R1_err, 'CPE1_Y': CPE1_Y_err, 'CPE1_n': CPE1_n_err, 'R2': R2_err, 'CPE2_Y': CPE2_Y_err, 'CPE2_n': CPE2_n_err, 'CPE3_Y': CPE3_Y_err, 'CPE3_n': CPE3_n_err},
                                                                    'chi2':{'fit': chi2, 'KK':chi2_KK}})
    else:
        R2_guess = abs(ReZ[ids_min[1]] - R1_guess - R0_guess)
        R2_min = abs(0.75*R2_guess)
        R2_max = abs(1.75*R2_guess)
        circuit_0='R_0-p(R_1,CPE_1)-p(R_2,CPE_2)-CPE_3'
        initial_guess_0=[R0_guess, R1_guess, 1e-10,0.98, R2_guess, 1e-6,0.9, 1e-6,0.9]
        bounds_0 = (R0_min, R1_min, 1e-13,0.001, R2_min, 1e-13,0.001, 1e-13,0.001),(R0_max, R1_max, 1e-8,1, R2_max, 1,1, 1,1)
        if len(ReZ)<4:
            R0, R1, CPE1_Y, CPE1_n, R2, CPE2_Y, CPE2_n, CPE3_Y, CPE3_n = ReZ[0], None, None, None, None, None, None, None, None
            R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, CPE3_Y_err, CPE3_n_err = None, None, None, None, None, None, None, None, None
            chi2, chi2_KK = None, None
        else:
            res_fit, uns_fit = circuits.fitting.circuit_fit(freq, Z, circuit=circuit_0, initial_guess=initial_guess_0, constants={}, bounds=bounds_0, weight_by_modulus=True, global_opt=False)
            R0, R1, CPE1_Y, CPE1_n, R2, CPE2_Y, CPE2_n, CPE3_Y, CPE3_n = res_fit[0], res_fit[1], res_fit[2], res_fit[3], res_fit[4], res_fit[5], res_fit[6], res_fit[7], res_fit[8]
            if isinstance(uns_fit, type(None)): 
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, CPE3_Y_err, CPE3_n_err = None, None, None, None, None, None, None, None, None
            else:
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, CPE3_Y_err, CPE3_n_err = uns_fit[0], uns_fit[1], uns_fit[2], uns_fit[3], uns_fit[4], uns_fit[5], uns_fit[6], uns_fit[7], uns_fit[8]
            ### chi2
            circuit_test = circuits.CustomCircuit(circuit=circuit_0, initial_guess=res_fit)
            Z_fit = circuit_test.predict(freq)
            chi2 = np.sum((Z_fit.real - Z.real)**2/(Z.real**2+Z.imag**2))+np.sum((Z_fit.imag - Z.imag)**2/(Z.real**2+Z.imag**2))
            M, mu, Z_linKK, res_real, res_imag = linKK(freq, Z, c=0.85, max_M=1000, fit_type='complex', add_cap=True)
            chi2_KK = np.sum((res_real)**2) + np.sum((res_imag)**2)
            ### plot
            plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
            plt.rcParams["axes.labelweight"] = "bold" # general thing
            fig, ax = plt.subplots(figsize=(9,6),dpi=100)
            scatter = ax.scatter(Z.real/1e3, -Z.imag/1e3, facecolors='none', edgecolors='b', linewidth = 1, s = 15, label = 'Data')
            line, = ax.plot(Z_fit.real/1e3, -Z_fit.imag/1e3, color='r', alpha = 1.00, linewidth = 1.5, label = 'Fit')
            max_ = 1.05*max(max(Z.real/1e3), max(-Z.imag/1e3))
            ax.set_xlim(xmin=0, xmax=max_)
            ax.set_ylim(ymin=0, ymax=max_)
            ax.set_aspect('equal', adjustable='box')
            tick_interval = np.round(max_ / 5, -int(np.floor(np.log10(max_ / 5))))
            tick_values = np.arange(0, max_ + tick_interval, tick_interval)
            ax.set_xticks(tick_values)
            ax.set_yticks(tick_values)
            ax.tick_params(which='both', labelsize=16, width=1.5)
            ax.set_xlabel("Z', kΩ", fontsize=20)
            ax.set_ylabel("-Z'', kΩ", fontsize=20)
            handles = [scatter, line, plt.Line2D([], [], color='none')]
            labels = ['Data', 'Fit', f'χ²: {chi2:.4f}']
            ax.legend(handles, labels, title=f"Run {int(run/4)}, cycle {int(run%4)}", title_fontsize='medium', prop={'size': 'medium'})
            plt.savefig( f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/EIS/eis_{int(run/4)}_{int(run%4)}.png", transparent=False)
            plt.clf()
            plt.close('all')
            #return
        retc = return_class(parameters={'addresses':address}, data={'res':{'R0': R0, 'R1': R1, 'CPE1_Y': CPE1_Y, 'CPE1_n': CPE1_n, 'R2': R2, 'CPE2_Y': CPE2_Y, 'CPE2_n': CPE2_n, 'CPE3_Y': CPE3_Y, 'CPE3_n': CPE3_n},
                                                                'err':{'R0': R0_err, 'R1': R1_err, 'CPE1_Y': CPE1_Y_err, 'CPE1_n': CPE1_n_err, 'R2': R2_err, 'CPE2_Y': CPE2_Y_err, 'CPE2_n': CPE2_n_err, 'CPE3_Y': CPE3_Y_err, 'CPE3_n': CPE3_n_err},
                                                                'chi2':{'fit': chi2, 'KK':chi2_KK}})
    return retc
    
@app.get("/analysis/eis1")
def eis1(run: int, address: str):
    global data
    ReZ_ = data[0][0]
    ImZ_ = data[0][1]
    freq_ = data[0][2]
    ReZ_ids = np.where(ReZ_ > 0)[0]
    ImZ_ids = np.where(ImZ_ > 0)[0]
    ids = [i for i in ImZ_ids if i in ReZ_ids]
    ReZ = ReZ_[ids]
    ImZ = ImZ_[ids]
    freq = freq_[ids]
    Z = np.array(ReZ)-np.array(ImZ)*1j
    angle = np.arctan(ImZ/ReZ)*90
    
    def local_minimum(data, threshold, window_size):
        filtered_data = [x if x < threshold else np.nan for x in data] # Filter out values above the threshold
        smoothed_data = np.convolve(filtered_data, np.ones(window_size), 'valid') / window_size # Smooth the data
        minimum_indices = [] # Find the local minimum indices
        for i in range(1, len(smoothed_data) - 1):
            if not np.isnan(smoothed_data[i]) and smoothed_data[i-1] > smoothed_data[i] < smoothed_data[i+1]:
                minimum_indices.append(i + window_size // 2)  # Adjust index for window size
                if len(minimum_indices) == 3:
                    break
        while len(minimum_indices) < 3: # Ensure the list has two elements, using None as a placeholder if necessary
            minimum_indices.append(None)
        return minimum_indices

    threshold = 90
    window_size = 5

    ids_min = local_minimum(angle, threshold, window_size)
    id0 = next((index for index, value in enumerate(angle) if value > 0), 0)
    R0_guess = 0.95*ReZ[id0]
    R0_min = 0.5*R0_guess
    R0_max = 1.05*R0_guess

    if ids_min[0] == None:
        R1_guess = 1000
        R1_min = 0
        R1_max = 100000
    else:
        R1_guess = abs(ReZ[ids_min[0]] - R0_guess)
        R1_min = abs(0.5*R1_guess)
        R1_max = abs(1.75*R1_guess)

    if ids_min[1] == None:
        R2_guess = 10000
        R2_min = 0
        R2_max = 5000000
    else:
        R2_guess = abs(ReZ[ids_min[1]] - R1_guess - R0_guess)
        R2_min = abs(0.75*R2_guess)
        R2_max = abs(2*R2_guess)

    if ids_min[2] == None:    
        circuit_1='R_0-p(R_1,CPE_1)-p(R_2-W_1,CPE_2)'
        initial_guess_1=[R0_guess, R1_guess, 1e-10,0.98, R2_guess,1e+5, 1e-6,0.9]
        bounds_1 = (R0_min, R1_min, 1e-13,0.001, R2_min,1e-1, 1e-13,0.001),(R0_max, R1_max, 1e-6,1, R2_max,1e+10, 1,1)
        if len(ReZ)<4:
            R0, R1, CPE1_Y, CPE1_n, R2, W1, CPE2_Y, CPE2_n = ReZ[0], None, None, None, None, None, None, None
            R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, W1_err, CPE2_Y_err, CPE2_n_err = None, None, None, None, None, None, None, None
            chi2, chi2_KK = None, None
        else:
            res_fit, uns_fit = circuits.fitting.circuit_fit(freq, Z, circuit=circuit_1, initial_guess=initial_guess_1, constants={}, bounds=bounds_1, weight_by_modulus=True, global_opt=False)
            R0, R1, CPE1_Y, CPE1_n, R2, W1, CPE2_Y, CPE2_n = res_fit[0], res_fit[1], res_fit[2], res_fit[3], res_fit[4], res_fit[5], res_fit[6], res_fit[7]
            if isinstance(uns_fit, type(None)): 
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, W1_err, CPE2_Y_err, CPE2_n_err = None, None, None, None, None, None, None, None
            else:
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, W1_err, CPE2_Y_err, CPE2_n_err = uns_fit[0], uns_fit[1], uns_fit[2], uns_fit[3], uns_fit[4], uns_fit[5], uns_fit[6], uns_fit[7]
            ###chi2
            circuit_test = circuits.CustomCircuit(circuit=circuit_1, initial_guess=res_fit)
            Z_fit = circuit_test.predict(freq)
            chi2 = np.sum((Z_fit.real - Z.real)**2/(Z.real**2+Z.imag**2))+np.sum((Z_fit.imag - Z.imag)**2/(Z.real**2+Z.imag**2))
            M, mu, Z_linKK, res_real, res_imag = linKK(freq, Z, c=0.85, max_M=1000, fit_type='complex', add_cap=True)
            chi2_KK = np.sum((res_real)**2) + np.sum((res_imag)**2)
            ### plot
            plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
            plt.rcParams["axes.labelweight"] = "bold" # general thing
            fig, ax = plt.subplots(figsize=(9,6),dpi=100)
            scatter = ax.scatter(Z.real/1e3, -Z.imag/1e3, facecolors='none', edgecolors='b', linewidth = 1, s = 15, label = 'Data')
            line, = ax.plot(Z_fit.real/1e3, -Z_fit.imag/1e3, color='r', alpha = 1.00, linewidth = 1.5, label = 'Fit')
            max_ = 1.05*max(max(Z.real/1e3), max(-Z.imag/1e3))
            ax.set_xlim(xmin=0, xmax=max_)
            ax.set_ylim(ymin=0, ymax=max_)
            ax.set_aspect('equal', adjustable='box')
            tick_interval = np.round(max_ / 5, -int(np.floor(np.log10(max_ / 5))))
            tick_values = np.arange(0, max_ + tick_interval, tick_interval)
            ax.set_xticks(tick_values)
            ax.set_yticks(tick_values)
            ax.tick_params(which='both', labelsize=16, width=1.5)
            ax.set_xlabel("Z', kΩ", fontsize=20)
            ax.set_ylabel("-Z'', kΩ", fontsize=20)
            handles = [scatter, line, plt.Line2D([], [], color='none')]
            labels = ['Data', 'Fit', f'χ²: {chi2:.4f}']
            ax.legend(handles, labels, title=f"Run {int(run/4)}, cycle {int(run%4)}", title_fontsize='medium', prop={'size': 'medium'})
            plt.savefig(f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/EIS/eis_{int(run/4)}_{int(run%4)}.png", transparent=False)
            plt.clf()
            plt.close('all')
            #return
        retc = return_class(parameters={'addresses':address}, data={'res':{'R0': R0, 'R1': R1, 'CPE1_Y': CPE1_Y, 'CPE1_n': CPE1_n, 'R2': R2, 'W1': W1, 'CPE2_Y': CPE2_Y, 'CPE2_n': CPE2_n},
                                                                        'err':{'R0': R0_err, 'R1': R1_err, 'CPE1_Y': CPE1_Y_err, 'CPE1_n': CPE1_n_err, 'R2': R2_err, 'W1': W1_err, 'CPE2_Y': CPE2_Y_err, 'CPE2_n': CPE2_n_err},
                                                                        'chi2':{'fit': chi2, 'KK':chi2_KK}})
    else:
        R3_guess = abs(ReZ[ids_min[2]] - R2_guess - R1_guess - R0_guess)
        R3_min = abs(0.75*R3_guess)
        R3_max = abs(2.25*R3_guess)
        circuit_1='R_0-p(R_1,CPE_1)-p(R_2,CPE_2)-p(R_3-W_1,CPE_3)'
        initial_guess_1=[R0_guess, R1_guess, 1e-10,0.98, R2_guess, 1e-10,0.98, R3_guess,1e+5, 1e-6,0.9]
        bounds_1 = (R0_min, R1_min, 1e-13,0.001, R2_min, 1e-13,0.001, R3_min,1e-1, 1e-13,0.001),(R0_max, R1_max, 1e-6,1, R2_max, 1e-6,1, R3_max,1e+10, 1,1)
        if len(ReZ)<4:
            R0, R1, CPE1_Y, CPE1_n, R2, CPE2_Y, CPE2_n, R3, W1, CPE3_Y, CPE3_n = ReZ[0], None, None, None, None, None, None, None, None, None, None
            R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, R3_err, W1_err, CPE3_Y_err, CPE3_n_err = None, None, None, None, None, None, None, None, None, None, None
            chi2, chi2_KK = None, None
        else:
            res_fit, uns_fit = circuits.fitting.circuit_fit(freq, Z, circuit=circuit_1, initial_guess=initial_guess_1, constants={}, bounds=bounds_1, weight_by_modulus=True, global_opt=False)
            R0, R1, CPE1_Y, CPE1_n, R2, CPE2_Y, CPE2_n, R3, W1, CPE3_Y, CPE3_n = res_fit[0], res_fit[1], res_fit[2], res_fit[3], res_fit[4], res_fit[5], res_fit[6], res_fit[7], res_fit[8], res_fit[9], res_fit[10]
            if isinstance(uns_fit, type(None)): 
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, R3_err, W1_err, CPE3_Y_err, CPE3_n_err = None, None, None, None, None, None, None, None, None, None, None
            else:
                R0_err, R1_err, CPE1_Y_err, CPE1_n_err, R2_err, CPE2_Y_err, CPE2_n_err, R3_err, W1_err, CPE3_Y_err, CPE3_n_err = uns_fit[0], uns_fit[1], uns_fit[2], uns_fit[3], uns_fit[4], uns_fit[5], uns_fit[6], uns_fit[7], uns_fit[8], uns_fit[9], uns_fit[10]
            ###chi2
            circuit_test = circuits.CustomCircuit(circuit=circuit_1, initial_guess=res_fit)
            Z_fit = circuit_test.predict(freq)
            chi2 = np.sum((Z_fit.real - Z.real)**2/(Z.real**2+Z.imag**2))+np.sum((Z_fit.imag - Z.imag)**2/(Z.real**2+Z.imag**2))
            M, mu, Z_linKK, res_real, res_imag = linKK(freq, Z, c=0.85, max_M=1000, fit_type='complex', add_cap=True)
            chi2_KK = np.sum((res_real)**2) + np.sum((res_imag)**2)
            ### plot
            plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
            plt.rcParams["axes.labelweight"] = "bold" # general thing
            fig, ax = plt.subplots(figsize=(9,6),dpi=100)
            scatter = ax.scatter(Z.real/1e3, -Z.imag/1e3, facecolors='none', edgecolors='b', linewidth = 1, s = 15, label = 'Data')
            line, = ax.plot(Z_fit.real/1e3, -Z_fit.imag/1e3, color='r', alpha = 1.00, linewidth = 1.5, label = 'Fit')
            max_ = 1.05*max(max(Z.real/1e3), max(-Z.imag/1e3))
            ax.set_xlim(xmin=0, xmax=max_)
            ax.set_ylim(ymin=0, ymax=max_)
            ax.set_aspect('equal', adjustable='box')
            tick_interval = np.round(max_ / 5, -int(np.floor(np.log10(max_ / 5))))
            tick_values = np.arange(0, max_ + tick_interval, tick_interval)
            ax.set_xticks(tick_values)
            ax.set_yticks(tick_values)
            ax.tick_params(which='both', labelsize=16, width=1.5)
            ax.set_xlabel("Z', kΩ", fontsize=20)
            ax.set_ylabel("-Z'', kΩ", fontsize=20)
            handles = [scatter, line, plt.Line2D([], [], color='none')]
            labels = ['Data', 'Fit', f'χ²: {chi2:.4f}']
            ax.legend(handles, labels, title=f"Run {int(run/4)}, cycle {int(run%4)}", title_fontsize='medium', prop={'size': 'medium'})
            plt.savefig(f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/EIS/eis_{int(run/4)}_{int(run%4)}.png", transparent=False)
            plt.clf()
            plt.close('all')
            #return
        retc = return_class(parameters={'addresses':address}, data={'res':{'R0': R0, 'R1': R1, 'CPE1_Y': CPE1_Y, 'CPE1_n': CPE1_n, 'R2': R2, 'CPE2_Y': CPE2_Y, 'CPE2_n': CPE2_n, 'R3': R3, 'W1': W1, 'CPE3_Y': CPE3_Y, 'CPE3_n': CPE3_n},
                                                                        'err':{'R0': R0_err, 'R1': R1_err, 'CPE1_Y': CPE1_Y_err, 'CPE1_n': CPE1_n_err, 'R2': R2_err, 'CPE2_Y': CPE2_Y_err, 'CPE2_n': CPE2_n_err, 'R3': R3_err, 'W1': W1_err, 'CPE3_Y': CPE3_Y_err, 'CPE3_n': CPE3_n_err},
                                                                        'chi2':{'fit': chi2, 'KK':chi2_KK}})
    return retc

@app.get("/analysis/cp")
### input: query (coordinates and theoretical capacities), measured x and y, CP Corrected time
### output: id, concentrations, x,y coordinates, measured capacity
def cp(query: str, address:str):
    global data
    print(data)
    query = json.loads(query)
    q_query = query['q_query']
    x_query = query['x_query']
    c_query = query['c_query']
    i_query = query['i_query']
    m_query = query['m_query']
    x = data[0][0]
    y = data[0][1]
    tc1 = data[0][2][:-4]
    Ic1 = data[0][3][:-4]
    Vc1 = data[0][4][:-4]
    td1 = data[0][5][:-4]
    Id1 = data[0][6][:-4]
    Vd1 = data[0][7][:-4]
    tc2 = data[0][8][:-4]
    Ic2 = data[0][9][:-4]
    Vc2 = data[0][10][:-4]
    td2 = data[0][11][:-4]
    Id2 = data[0][12][:-4]
    Vd2 = data[0][13][:-4]
    tc3 = data[0][14][:-4]
    Ic3 = data[0][15][:-4]
    Vc3 = data[0][16][:-4]
    td3 = data[0][17][:-4]
    Id3 = data[0][18][:-4]
    Vd3 = data[0][19][:-4]
    key_x = [data[0][0], data[0][1]]
    id = x_query.index(key_x)
    c = c_query[id]
    c1, c2, c3 = c[0], c[1], c[2]
    Q1 = td1[-1]*q_query[id]*np.mean(Id1)/i_query[id]/3600
    Q2 = td2[-1]*q_query[id]*np.mean(Id2)/i_query[id]/3600
    Q3 = td3[-1]*q_query[id]*np.mean(Id3)/i_query[id]/3600
    print(Q3)
    M_an = m_query[id]
    M_cat = q_query[id]*m_query[id]/147 # 147 = Q(LiNiMnO2)
    if len(td1) > 4:
        V_av1 = simpson(Vd1, td1)/td1[-1]
        E1 = (4.7 * td1[-1] - simpson(Vd1, td1))/3600 * np.mean(Id1) / (M_an + M_cat) * 1000 
        CE1 = np.mean(Id1)*td1[-1]/np.abs(np.mean(Ic1))/tc1[-1]
        VE1 = (4.7 - simpson(Vd1, td1)/td1[-1])/(4.7 - simpson(Vc1, tc1)/tc1[-1])
        EE1 = VE1*CE1
    else:
        V_av1, E1, CE1, VE1, EE1 = 0, 0, 0, 0, 0
    if len(td2) > 4:
        V_av2 = simpson(Vd2, td2)/td2[-1]
        E2 = (4.7 * td2[-1] - simpson(Vd2, td2))/3600 * np.mean(Id2) / (M_an + M_cat) * 1000  
        CE2 = np.mean(Id2)*td2[-1]/np.abs(np.mean(Ic2))/tc2[-1]
        VE2 = (4.7 - simpson(Vd2, td2)/td2[-1])/(4.7 - simpson(Vc2, tc2)/tc2[-1])
        EE2 = VE2*CE2
    else:
        V_av2, E2, CE2, VE2, EE2 = 0, 0, 0, 0, 0
    if len(td3) > 4:
        V_av3 = simpson(Vd3, td3)/td3[-1]
        E3 = (4.7 * td3[-1] - simpson(Vd3, td3))/3600 * np.mean(Id3) / (M_an + M_cat) * 1000   
        CE3 = np.mean(Id3)*td3[-1]/np.abs(np.mean(Ic3))/tc3[-1]
        VE3 = (4.7 - simpson(Vd3, td3)/td3[-1])/(4.7 - simpson(Vc3, tc3)/tc3[-1])
        EE3 = VE3*CE3
    else:
        V_av3, E3, CE3, VE3, EE3 = 0, 0, 0, 0, 0
    retc = return_class(parameters={'addresses':address}, 
                        data={'id':{'id': id}, 
                              'C':{'c1': c1, 'c2': c2, 'c3': c3},
                              'X':{'x': x, 'y': y}, 
                              'Y':{'Q1': Q1, 'E1': E1, 'V_av1': V_av1,
                                   'Q2': Q2, 'E2': E2, 'V_av2': V_av2,
                                   'Q3': Q3, 'E3': E3, 'V_av3': V_av3}, 
                              'Efficiencies': {'CE1': CE1, 'VE1': VE1, 'EE1': EE1,
                                               'CE2': CE2, 'VE2': VE2, 'EE2': EE2,
                                               'CE3': CE3, 'VE3': VE3, 'EE3': EE3}})
    return retc



"""
@app.get("/analysis/dummy")
def bridge(exp_num: str, sources: str): #
    For now this is just a pass throught function that can get the result from measure action file and feed to ml server

    Args:
        exp_num (float): [this is the experimental number]
        key_y (float): [This is the result that we get from schwefel function, calculated in the measure action] 

    Returns:
        [dictionaty]: [measurement area (x_pos, y_pos) and the schwefel function result]
    

    if sources == "session":
        sources = requests.get("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'], 
                config['servers']['orchestrator']['port'], 'orchestrator', 'getSession'), params=None).json()
        print(sources)
    else:
        try:
            sources = json.loads(sources)
            if "session" in sources:
                sources[sources.index("session")] = requests.get("http://{}:{}/{}/{}".format(config['servers']['orchestrator']['host'], 
                config['servers']['orchestrator']['port'], 'orchestrator', 'getSession'), params=None).json()
        except:
            pass

    with open('C:/Users/LaborRatte23-3/Documents/session/sessionAnalysis.pck', 'rb') as banana:
        sources = pickle.load(banana)
    # here we need to return the key_y which is the schwefel function result and the corresponded measurement area
    # i.e pos: (dx, dy) -> schwefel(dx, dy)
    # We need to get the index of the perfomed experiment
    print(sources)
    if type(exp_num) == str:
        exp_num = exp_num.split('_')[-1]
    #session = json.loads(sources)
    data = interpret_input(
        sources, "session", "schwefelFunction/data/data/key_y", experiment_numbers=int(exp_num))
    print(data)

    print(exp_num)

    #data = interpret_input(session,"session","dummy/data/key_y")
    retc = dict(
        parameters={'exp_num': exp_num}, data=data) #(x, y)
    # {'key_x': 'measurement_no_{}/motor/moveSample_0'.format(exp_num), 'key_y': key_y})
    return retc


def interpret_input(sources, types, addresses, experiment_numbers=None):
    # sources is a single data source (jsonned object or file address) or a jsonned list of data sources
    # type is a string or jsonned list of strings telling you what data format(s) you are reading in
    # possible inputs: list of or individual kadi records, local files, the current session, pure data
    # source values for these: kadi id's, filepaths strings, a dictionary, a list or dictionary or whatever
    # type values for these: "kadi","file","session","pure"
    # well, actually, there will be no "file" type, instead, will need different codes for different file extensions ("json", "hdf5", etc.) (right now "hdf5" is the only one that works)
    # addresses tells you where in an HDF5 file to pull the data from, will be a single address or list of addresses
    # if data type is "pure", addresses will be None, as no processing is required.
    # if data is neither preprocessed nor in our standardized .hdf5 format, I guess I will have to modify this to accommodate later.
    # when we are working with an HDF5, as we should be in most cases, we will automatically iterate over every measurement number in the most recent session
    # addresses will tell us how to get from the measurment number root to each value we want
    # addresses will be a string of keys separated by /'s. the topmost key (action name) will ignore trailing numbers + underscore
    # if multiple of a single type of action are in the measurment, it will by default grab the lowest number; add "_i" to specify the (i+1)th lowest

    # we need the ability to only grab certain measurements from the input data source(s).
    # currently, I am going to have the choice defined by the integer "measurement_no" in the names of the given dictionary keys.
    # thus, the input "experiment_numbers", will comprise an integer or jsonned list thereof.
    # this means that this feature probably won't be compatible with using multiple data sources at once, but for now, I do not think it needs to be.
    # when I have finished code which I can demonstrate, it should be easier to get intelligent feedback as to what would be a better standard.
    print(sources)
    try:
        sources = json.loads(sources)
    except:
        pass
    try:
        types = json.loads(types)
    except:
        pass
    try:
        addresses = json.loads(addresses)
    except:
        pass
    try:
        experiment_numbers = json.loads(experiment_numbers)
    except:
        pass
    if isinstance(types, str):
        sources, types = [sources], [types]
    if isinstance(addresses, str):
        addresses = [addresses]
    if isinstance(experiment_numbers, int) or experiment_numbers == None:
        experiment_numbers = [experiment_numbers]
    datas = {address.split('/')[-1]:[] for address in addresses}
    for source, typ in zip(sources, types):
        if typ == "kadi":
            requests.get(f"{kadiurl}/data/downloadfilesfromrecord",
                         params={'ident': source, 'filepath': filepath})
            source = os.path.join(filepath, source+".hdf5")
        if typ in ("kadi", "hdf5"):
            source = dict(hdfdict.load(source, lazy=False, mode="r+"))
        if typ in ("kadi", "hdf5", "session"):
            data = dict()
            run = highestName(
                list(filter(lambda k: k != 'meta', source.keys())))
            # maybe it would be better to sort keys before iterating over them
            
            for address in addresses:
                datum = []
                topadd = address.split('/')[0].split('_')
                for key in source[run].keys():
                    if key != 'meta' and (experiment_numbers == [None] or int(key.split('_')[-1]) in experiment_numbers):
                        # possibilities: address has no number and key(s) do
                        #               multiple numbered addresses and keys
                        actions = sorted(list(filter(lambda a: a.split('_')[
                                         0] == topadd[0], source[run][key].keys())), key=lambda a: int(a.split('_')[1]))
                        try:
                            if len(topadd) > 1:
                                action = actions[int(topadd[1])]
                            else:
                                action = actions[0]
                            datum.append(dict_address(
                                '/'.join(address.split('/')[1:]), source[run][key][action]))
                        except:
                            print(
                                f"item {key} does not have what we are looking for")
                data.update({address.split('/')[-1]:datum})
            source = data
        if typ in ("kadi", "hdf5", "session", "pure"):
            datas = {key:datas[key] + source[key] for key in datas.keys()}
    return datas
"""

if __name__ == "__main__":
    url = config[serverkey]['url']
    uvicorn.run(app, host=config['servers'][serverkey]['host'], 
                     port=config['servers'][serverkey]['port'])
    
    # url = "http://{}:{}".format(config['servers']['analysisDriver']
    #                             ['host'], config['servers']['analysisDriver']['port'])
    # print('Port of analysisDriver: {}')
    # uvicorn.run(app, host=config['servers']['analysisDriver']
    #             ['host'], port=config['servers']['analysisDriver']['port'])
    # print("instantiated analysisDriver")
