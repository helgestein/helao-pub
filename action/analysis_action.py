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
    data = [] #don't need to load the data from pervious exp
    try:
        address = json.loads(address)
    except:
        address = [address]
    newdata = []
    #print(address)
    for add in address:
        with h5py.File(path, 'r') as h5file:
            add = f'run_{run}/'+add+'/'
            print(add)
            if isinstance(h5file[add],h5py.Group):
                newdata.append(hdf5_group_to_dict(h5file, add))
            else:
                newdata.append(h5file[add][()])
    #print(f"data is {newdata}")
    data.append(newdata[0] if len(newdata) == 1 else newdata)
    #print(f'Data is {data}')

@app.get("/analysis/dummy")
def schwefel_bridge(x_address:str,y_address:str,schwefel_address:str):
    x = data[x_address]
    y = data[y_address]
    schwefel = data[schwefel_address]
    retc = return_class(parameters={'x_address':x_address,'y_address':y_address,'schwefel_address':schwefel_address},
                        data={'x':{'x':x,'y':y},'y':{'schwefel':schwefel}})
    return retc

@app.get("/analysis/ocp")
### input: OCP data
### output: mean OCP value and error
def ocp(address:str):
    global data
    time = config[serverkey]['ocp']['analysis_points']
    ocp = data[0][0][:-4][-time:]
    ocp_res, ocp_err = np.mean(ocp), 2*np.std(ocp)
    retc = return_class(parameters={'addresses':address}, data={'ocp_val': ocp_res, 'ocp_err': ocp_err})
    return retc

@app.get("/analysis/cp")
### input: chronopotentiometry data (charge and discharge time, current and voltage)
### output: measured capacity, coulombic, voltage and energy efficiencies 
def cp(query: str, address:str):
    global data
    counter_voltage = config[serverkey]['cp']['counter_voltage']
    tc1, Ic1, Vc1 = data[0][0][:-4], data[0][1][:-4], data[0][2][:-4]
    td1, Id1, Vd1 = data[0][3][:-4], data[0][4][:-4], data[0][5][:-4]
    Qc, Qd = tc1[-1]/3600*abs(np.mean(Ic1)), td1[-1]/3600*abs(np.mean(Id1)) # Ah
    CE = 100*Qd/Qc #in %
    VE = 100*(counter_voltage - simpson(Vd1, td1)/td1[-1])/(counter_voltage - simpson(Vc1, tc1)/tc1[-1]) #in %
    EE = CE*VE/100 #in %
    retc = return_class(parameters={'addresses':address},
                        data={'Qc': Qc, 'Qd': Qd, 'CE': CE, 'VE': VE, 'EE': EE})
    return retc

@app.get("/analysis/eis")
### input: EIS data (list of ReZ, ImZ, freq)
### output: best circuit, resistance values, uncertainties, metric value, chi2_KK + plotting
def eis(run: int, address: str):
    global data
    
    ### load config params for fitting
    circuit_list = config[serverkey]['eis']['circuit_list']
    guess_list = config[serverkey]['eis']['guess_list']
    bounds_list = config[serverkey]['eis']['bounds_list']
    semicircles_max = config[serverkey]['eis']['semicircles_max']
    metric = config[serverkey]['eis']['metric']
    save_path = config[serverkey]['eis']['path']

    ### load data: need to provide as an address paths to ReZ, ImZ and freq data
    ReZ_, ImZ_, freq_ = data[0][0], data[0][1], data[0][2]
    ReZ_ids, ImZ_ids = np.where(ReZ_ > 0)[0], np.where(ImZ_ > 0)[0]
    ids = [i for i in ImZ_ids if i in ReZ_ids]
    ReZ, ImZ, freq = ReZ_[ids], ImZ_[ids], freq_[ids]
    Z = np.array(ReZ)-np.array(ImZ)*1j
    angle = np.arctan(ImZ/ReZ)*90

    ### generate initial guesses, bounds for R values
    threshold = 90
    window_size = 5
    ids_min = EISAnalyzer.local_minimum(angle, threshold, window_size, semicircles_max)
    R_guesses, R_mins, R_maxs = [], [], []
    R_guesses.append(0.95*ReZ[0]), R_mins.append(0.5*ReZ[0]), R_maxs.append(1.05*ReZ[0])
    for i in range(3):
        if ids_min[i] == None:
            R_guesses.append(np.random.uniform(ReZ.min(), ReZ.max()))
            R_mins.append(0), R_maxs.append(10*ReZ.max())
        else:
            R_guesses.append(abs(ReZ[ids_min[i]] - sum(R_guesses)))
            R_mins.append(abs(0.5*R_guesses[i])), R_maxs.append(abs(2.5*R_guesses[i]))
    
    ### substitute placeholders with actual values
    substituted_guesses = EISAnalyzer.substitute_with_list(guess_list, R_guesses)
    substituted_bounds = EISAnalyzer.substitute_bounds_with_list(bounds_list, R_mins, R_maxs)

    ### data fitting
    if len(ReZ)<4:
        best_circuit = 'R_0'
        best_fit = [ReZ[0]]
        best_uns = None
        best_metric_value, chi2_KK = None, None
    else:
        best_circuit, best_fit, best_uns, best_metric_value, chi2_KK, Z_fit = EISAnalyzer.fit_and_select_best_circuit(freq, Z, circuit_list, substituted_guesses, substituted_bounds, metric)
        EISAnalyzer.plotting(Z, Z_fit, best_metric_value, metric, save_path, run)
        
    retc = return_class(parameters={'addresses':address}, 
                    data={'circuit': best_circuit, 'res': best_fit, 'uns': best_uns, 
                          'metric': best_metric_value, 'chi2_KK': chi2_KK})
    return retc

class EISAnalyzer:
    @staticmethod
    def local_minimum(data, threshold, window_size, semicircles_max):
        ### find local minimums of angle (phase) corresponding to the approximate R values, return their indices
        filtered_data = [x if x < threshold else np.nan for x in data] # Filter out values above the threshold
        smoothed_data = np.convolve(filtered_data, np.ones(window_size), 'valid') / window_size # Smooth the data
        minimum_indices = [] # Find the local minimum indices
        for i in range(1, len(smoothed_data) - 1):
            if not np.isnan(smoothed_data[i]) and smoothed_data[i-1] > smoothed_data[i] < smoothed_data[i+1]:
                minimum_indices.append(i + window_size // 2)  # Adjust index for window size
                if len(minimum_indices) == semicircles_max:
                    break
        while len(minimum_indices) < semicircles_max: # Ensure the list has two elements, using None as a placeholder if necessary
            minimum_indices.append(None)
        return minimum_indices
    
    @staticmethod
    def substitute_with_list(guess_list, R_guesses):
        ### substitute placeholders with actual values
        substituted_guesses = []
        for guesses in guess_list:
            # Replace placeholders in guesses
            substituted = [R_guesses[int(item[1:])] if isinstance(item, str) and item.startswith("R") else item for item in guesses]
            substituted_guesses.append(substituted)
        return substituted_guesses
    
    @staticmethod
    def substitute_bounds_with_list(bounds_list, R_mins, R_maxs):
        substituted_bounds = []
        for bounds in bounds_list:
            lower_bound, upper_bound = bounds
            # Replace placeholders in lower bound using R_mins
            substituted_lower_bound = [R_mins[int(item[1:])] if isinstance(item, str) and item.startswith("R") else item for item in lower_bound]
            # Replace placeholders in upper bound using R_maxs
            substituted_upper_bound = [R_maxs[int(item[1:])] if isinstance(item, str) and item.startswith("R") else item for item in upper_bound]
            # Append the substituted bounds as a tuple
            substituted_bounds.append((substituted_lower_bound, substituted_upper_bound))
        return substituted_bounds
    
    @staticmethod
    def fit_and_select_best_circuit(freq, Z, circuit_list, substituted_guesses, substituted_bounds, metric):
        ### metrics can be selected from 'chi2' or 'rmse'
        ### data fitting and selecting the best circuit based on the metric
        best_circuit, best_fit, best_uns = None, None, None
        best_metric_value = float('inf')
        for i, circuit in enumerate(circuit_list):
            initial_guess = substituted_guesses[i]
            bounds = substituted_bounds[i]
            try:
                # Fit the circuit using the initial guess and bounds
                res_fit, uns_fit = circuits.fitting.circuit_fit(freq, Z, circuit=circuit, initial_guess=initial_guess, constants={}, 
                                                                bounds=bounds, weight_by_modulus=True, global_opt=False)
                circuit_test = circuits.CustomCircuit(circuit=circuit, initial_guess=res_fit)
                Z_fit = circuit_test.predict(freq)
                rmse = np.sqrt(np.mean(np.abs(Z_fit - Z) ** 2))
                chi2 = np.sum((Z_fit.real - Z.real) ** 2 / (Z.real ** 2 + Z.imag ** 2)) + \
                    np.sum((Z_fit.imag - Z.imag) ** 2 / (Z.real ** 2 + Z.imag ** 2))
                M, mu, Z_linKK, res_real, res_imag = linKK(freq, Z, c=0.85, max_M=1000, fit_type='complex', add_cap=True)
                chi2_KK = np.sum((res_real) ** 2) + np.sum((res_imag) ** 2)
                if metric == 'chi2':
                    current_metric_value = chi2
                elif metric == 'rmse':
                    current_metric_value = rmse
                else:
                    raise ValueError("Invalid metric. Choose from 'chi2' or 'rmse'.")
                #print(f"Circuit {i + 1}: {circuit}")
                #print(f"RMSE: {rmse:.2f}, chi2: {chi2:.2e}. Selected Metric: {metric}")
                if current_metric_value < best_metric_value:
                    best_circuit = circuit
                    best_fit, best_uns = res_fit, uns_fit
                    best_metric_value = current_metric_value
            except Exception as e:
                print(f"Fitting failed for circuit {circuit}: {e}")
                continue
        #print(f"The best circuit: {best_circuit}, with metric value: {best_metric_value:.2e} and chi2_KK of data: {chi2_KK:.2e}")
        return best_circuit, best_fit, best_uns, best_metric_value, chi2_KK, Z_fit

    @staticmethod
    def plotting(Z, Z_fit, best_metric_value, metric, path, run):
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
        if metric == 'chi2':
            labels = ['Data', 'Fit', f'χ²: {best_metric_value:.4f}']
        else:
            labels = ['Data', 'Fit', f'RMSE: {best_metric_value:.2f}']
        ax.legend(handles, labels, title=f"Run {int(run/4)}, cycle {int(run%4)}", title_fontsize='medium', prop={'size': 'medium'})
        plt.savefig(f"{path}/eis_{int(run/4)}_{int(run%4)}.png", transparent=False)
        plt.clf()
        plt.close('all')

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
