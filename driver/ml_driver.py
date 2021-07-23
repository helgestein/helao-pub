import json

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from sklearn.ensemble import RandomForestRegressor
import sys
sys.path.append(r"../")

from celery_conf import app
from time import sleep
from util import highestName, dict_address

# for the test we just need active_learning_random_forest_simulation function
kadiurl = None
filepath = "C:/Users/jkflowers/Downloads"


class DataUtilSim:
    def __init__(self):
        return

    # changed to the staticmethod because inside of the tasks we can't call anything from self as a DataUtilSim instance
    @staticmethod
    # name argument is required because of the project structure
    @app.task(name='driver.ml_driver.gaus_model')
    def gaus_model(length_scale=1, restart_optimizer=10, random_state=42):
        """
        Define the gaussian process regressor
        :param self: instantiation
        :param length_scale: length scale
        :param restart_optimizer: number of times the optimizer restarts
        :param random_state: randomization
        :return: Gaus Model
        """
        kernel = 1 + Matern(length_scale=length_scale,
                            nu=3 / 2) + WhiteKernel(noise_level=1)
        model = GaussianProcessRegressor(alpha=1e-10, copy_X_train=True,
                                         kernel=kernel, n_restarts_optimizer=restart_optimizer, normalize_y=False,
                                         optimizer='fmin_l_bfgs_b', random_state=random_state)
        return model

    # changed to the staticmethod because inside of the tasks we can't call anything from self as a DataUtilSim instance
    @staticmethod
    # name argument is required because of the project structure
    @app.task(name='driver.ml_driver.gaussian_simulation')
    def gaussian_simulation(X, y, save_data_path='ml_data/ml_analysis.json'):
        """
        Gaussian algorithm and computing mean, variance and alpha value
        :param X: Input Data, python or np array
        :param y: Output data, python or np array
        :param save_data_path: Path to the file to save data to
        :return: Data uncertainty, mean and variance
        """
        if type(X) != np.ndarray:
            X = np.array(X['steps'])
        if type(y) != np.ndarray:
            y = np.array(y)

        model = self.gaus_model().fit(X, y)
        alpha = model.alpha_
        mu, var = model.predict(X, return_std=True)

        result = (alpha.tolist(), mu.tolist(), var.tolist())

        with open(save_data_path, 'w') as f:
            json.dump(result, f)

        return result

    #@staticmethod
    #@app.task(name='driver.ml_driver.gaussian_simulation')
    def active_learning_random_forest_simulation(self, query, data):#, addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
        # this is how the data is created in the analyis action and should be transfer here
        # data format: data={'x':{'x':d[0],'y':d[1]},'y':{'schwefel':d[2]}}
        # an example
        # data = [{'x': {'x': 1, 'y': 2}, 'y':{'schwefel': .1}}},{'x': {'x': 2, 'y': 4}, 'y':{'schwefel': .5}}}]
        """[summary]

        Args:
            key_x ([type]): [the accumulated position that machine was there]
            key_y ([type]): [the last value of schwefel function that we got]
            x_query ([type]): [list of all postions that we need to evaluate]
            y_query ([type]): [list of all calculated schwefel values according to x_query]
            save_data_path (str, optional): [description]. Defaults to 'ml_data/ml_analysis.json'.

        Returns:
            [x_suggest]: [position of the next experiment]
        """
        #session = json.loads(session)
        #print(session)
        #print(addresses)
        #data = interpret_input(
        #    session, "session", json.loads(addresses))
        #print(data)
        x_query = query['x_query']
        y_query = query['y_query']
        x = [dat['x']['x'] for dat in data]
        y = [dat['x']['y'] for dat in data]
        key_x = np.array([[i,j] for i, j in zip(x,y)])
        #key_x = [[eval(d[2])[0], eval(d[2])[1]] for d in data]
        #print(f"key_x: {key_x[0]}")
        # accumulated result at every step (n+1)
        #y_query = [d[1] for d in data]
        key_y = [dat['y']['schwefel'] for dat in data]
        #print(f"y_query: {y_query}")
        # we still need to check the format of the data
        # if x_query and y_query are string then:
        #x_query = json.loads(x_query)  # all the points of exp

        # the key_x should be in following [[4, 5], [4, 6]...]
        #key_x = np.array([[i, j] for i, j in zip(key_x['dx'], key_x['dy'])])

        # define a random forest regressor containing 50 estimators
        regr = RandomForestRegressor(n_estimators=50, random_state=1337)

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        test_ix = [i for i in range(len(x_query))]
        #train_ix = [np.random.choice(quin.shape[0], 1, replace=False)[0]]
        # we have the  first pos now (the initial point that motor goes there)
        train_ix = [np.where(x_query == j)[0][0] for j in key_x]
        print(f"train_ix: {train_ix}")
        # move the motor to the first point

        # we no longer need to put it in for loop
        # for i_ in tqdm(range(len(x_query))):
        # if i_ == 0:
        #    print(x_query[train_ix[-1]])
        # motor should go to the first random position
        # else:
        # move to the last added train position and pretend we meaure there
        # the actual value that was added in the last learning cycle is quin[train[-1]]
        regr.fit(x_query[train_ix], y_query[train_ix])
        pred = regr.predict(x_query[test_ix])

        y_var = np.zeros([50, len(x_query[test_ix])])

        for j in range(50):
            y_var[j, :] = regr.estimators_[j].predict(x_query[test_ix])

        aqf = pred+np.var(y_var, axis=0)

        ix = np.where(aqf == np.max(aqf))[0]
        print(f"aqf : {ix}")
        i = np.random.choice(ix)
        print(f"chosen random : {i}")
        train_ix.append(test_ix.pop(i))
        # next position that motor needs to go
        print(f"next position is : {x_query[train_ix[-1]].tolist()}")
        next_exp = x_query[train_ix[-1]].tolist()

        print(f"predicitons are {pred}")
        #For the sake of tracibility, we need to save the predicitons at every step 
        #for i in test_ix:
            #print(f"Are you float ?! {i}")
            #prediction.update({json.dumps(x_query[{}]).format(i): pred[i]})
        return next_exp[0], next_exp[1], next_exp


def interpret_input(sources: str, types: str, addresses: str, experiment_numbers=None):
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

    datas = []
    for source, typ in zip(sources, types):
        if typ == "kadi":
            requests.get(f"{kadiurl}/data/downloadfilesfromrecord",
                         params={'ident': source, 'filepath': filepath})
            source = os.path.join(filepath, source+".hdf5")
        if typ in ("kadi", "hdf5"):
            source = dict(hdfdict.load(source, lazy=False, mode="r+"))
        if typ in ("kadi", "hdf5", "session"):
            data = []
            run = highestName(
                list(filter(lambda k: k != 'meta', source.keys())))
            # maybe it would be better to sort keys before iterating over them
            for key in source[run].keys():
                if key != 'meta' and (experiment_numbers == [None] or key.split('_')[-1] in experiment_numbers):
                    datum = []
                    for address in addresses:
                        # possibilities: address has no number and key(s) do
                        #               multiple numbered addresses and keys
                        topadd = address.split('/')[0].split('_')
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
                    if datum != []:
                        data.append(datum)
            source = data
        if typ in ("kadi", "hdf5", "session", "pure"):
            datas += source
    return datas
