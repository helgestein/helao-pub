import pickle
from util import highestName, dict_address
from time import sleep
from celery_conf import app
import json
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import random
import sys
sys.path.append(r"../")

# for the test we just need active_learning_random_forest_simulation function
kadiurl = None
filepath = "C:/Users/jkflowers/Downloads"


class DataUtilSim:
    def __init__(self):
        return

    # changed to the staticmethod because inside of the tasks we can't call anything from self as a DataUtilSim instance
    # @staticmethod
    # name argument is required because of the project structure
    # @app.task(name='driver.ml_driver.gaus_model')

    def gaus_model(self, length_scale=1, nu_val=3/2, restart_optimizer=10, random_state=42):
        """
        Define the gaussian process regressor
        :param self: instantiation
        :param length_scale: length scale
        :param restart_optimizer: number of times the optimizer restarts
        :param random_state: randomization
        :return: Gaus Model
        """
        kernel = 1 + Matern(length_scale=length_scale,
                            nu=nu_val) + WhiteKernel(noise_level=1)
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


    def schwefel_function(self, x, y):
        comp = np.array([x, y])
        sch_comp = 20 * np.array(comp) - 500
        result = 0
        for index, element in enumerate(sch_comp):
            #print(f"index is {index} and element is {element}")
            result += - element * np.sin(np.sqrt(np.abs(element)))
        result = (-result) / 1000
        #const = 418.9829*2
        # const = (420.9687 + 500) / 20
        #result = result + const
        # result = (-1)*result
        return result

    # @staticmethod
    # @app.task(name='driver.ml_driver.gaussian_simulation')
    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
    def active_learning_random_forest_simulation_parallel(self, name, num, query, data, awaitedpoints):
        """[summary]

        Returns:
            [x_suggest]: [position of the next experiment]
        """
        # print(f"data is {data}")
        # query = json.loads(query)
        # #awaitedpoints = json.loads(awaitedpoints)
        # #print(f"the awaiting points are {awaitedpoints}")
        # x_query = query['x_query']
        # print(f"x query is {x_query} and the length of it is {len(x_query)}")
        # x_query =list(filter(lambda x: x not in awaitedpoints, x_query))
        # #print(f"x_query without awaited points are {x_query} and the length of it is {len(x_query)}")
        # #print(f"awaitedpoints are {awaitedpoints} and x_query is {x_query}")
        # y_query = query['y_query']
        # print(f"y_query is the other dude {y_query} and the length of it is {len(y_query)}")
        # x = [dat['x']['x'] for dat in data]
        # y = [dat['x']['y'] for dat in data]
        # print(f"length of x and y are {len(x)} and  {len(y)} and their values are {x} and {y}")
        # key_x = np.array([[i, j] for i, j in zip(x, y)])
        # print(f"the current points (key_x) are {key_x}")
        # key_y = [dat['y']['schwefel'] for dat in data]

        random.seed(25)
        awaitedpoints = json.loads(awaitedpoints)
        awaitedpoints = [[i['x'],i['y']] for i in awaitedpoints]
        print(f"the awaiting points are {awaitedpoints}")
        query = json.loads(query)
        x_query = query["x_query"]
        #x_query = list(filter(lambda x: x not in awaitedpoints, x_query))
        y_query = [self.schwefel_function(x[0], x[1])for x in x_query]
        #y_query_all = query["y_query"]
        key_x = [[dat['x']['x'], dat['x']['y']] for dat in data]
        print(f"data is {data}, key_x or current points are {key_x} and the x query is {x_query}")
        train_ix = [x_query.index(j) for j in key_x]
        #train_ix = [np.where(x_query == j)[0] for j in key_x]
        test_ix = [x_query.index(i) for i in x_query if i not in key_x and i not in awaitedpoints]

        # define a random forest regressor containing 50 estimators
        regr = RandomForestRegressor(n_estimators=50, random_state=36)

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        # test_ix = [i for i in range(len(x_query))]
        # print(f"test indeces are {test_ix}")
        # train_ix = [np.where(x_query == j)[0] for j in key_x]
        # print(f"the train indeces are {train_ix}  and the train data are {x_query[train_ix]}")


        print(f"the train indeces are {train_ix} and the train data are {x_query[train_ix]}and test indeces are {test_ix}")

        regr.fit(x_query[train_ix], y_query[train_ix])
        pred = regr.predict(x_query[test_ix])

        y_var = np.zeros([50, len(x_query[test_ix])])

        for j in range(50):
            y_var[j, :] = regr.estimators_[j].predict(x_query[test_ix])

        aqf = pred+np.var(y_var, axis=0)

        ix = np.where(aqf == np.max(aqf))[0]
        print(f"aqf : {ix}")
        i = np.random.choice(ix)
        print(f"indeces for the next experiment are {i}")
        print(f"train indeces before popping {train_ix}")

        self.plot_aqf(name, num, aqf, i, x_query, test_ix)
        train_ix.append(test_ix.pop(i))

        print(f"Train indeces are {train_ix}")
        # x_grid, y_grid = np.meshgrid(
        #     [2.5 * i for i in range(21)], [2.5 * i for i in range(21)])
        # schwefel_grid = np.array(y_query_all).reshape(21, 21)
        # self.plot_target(name, num, x_grid, y_grid,
        #                  schwefel_grid, x_query, train_ix, ind=-1)
        
        next_exp = x_query[train_ix[-1]].tolist()
        print(f"next first position is : {next_exp}")

        return next_exp[0], next_exp[1]  # , next_exp_2[0], next_exp_2[1]

    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
    def active_learning_gaussian_simulation_parallel(self, name, num, query, data, exp_exl_ratio=0.4):

        query = json.loads(query)

        x_query = query['x_query']
        y_query = query['y_query']

        x = [dat['x']['x'] for dat in data]
        y = [dat['x']['y'] for dat in data]
        key_x = np.array([[i, j] for i, j in zip(x, y)])

        key_y = [dat['y']['schwefel'] for dat in data]

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        test_ix = [i for i in range(len(x_query))]

        train_ix = [np.where(x_query == j)[0][0] for j in key_x]

        regr = self.gaus_model()
        regr.fit(x_query[train_ix], y_query[train_ix])

        y_mean, y_var = regr.predict(x_query[test_ix], return_std=True)
        aqf = exp_exl_ratio * y_mean + (1 - exp_exl_ratio) * y_var

        ix = np.where(aqf == np.max(aqf))[0]
        print(f"length od indees are {len(ix)} and they are {ix}")
        if len(ix) == 1:
            i = np.random.choice(ix, size=2, replace=True)
        else:
            i = np.random.choice(ix, size=2, replace=False)
        print(f"indeces for the next experiment are {i[0]} and {i[1]}")
        print(f"train indeces before popping {train_ix}")
        #print(f"chosen random : {i}")

        self.plot_aqf("{}".format(num), aqf, i[0], x_query, test_ix)
        self.plot_variance("{}".format(num), y_var, i[0], x_query, test_ix)

        #self.plot_aqf("sdc_2_{}".format(num) , aqf, i[1], x_query, test_ix)
        #self.plot_variance("sdc_2_{}".format(num), y_var, i[1], x_query, test_ix)

        train_ix.append(test_ix.pop(i[0]))
        train_ix.append(test_ix.pop(i[1]))

        print(f"Train indeces are {train_ix}")
        x_grid = np.array(query['x_grid'])
        y_grid = np.array(query['y_grid'])
        z_con = np.array(query['z_con'])

        self.plot_target("{}".format(num), x_grid, y_grid,
                         z_con, x_query, train_ix, ind=-1)
        #self.plot_target("sdc_2_{}".format(num), x_grid, y_grid, z_con, x_query, train_ix, ind=-2)

        # next position that motor needs to go
        print(f"next first position is : {x_query[train_ix[-1]].tolist()}")
        print(f"next second position is: {x_query[train_ix[-2]].tolist()} ")
        next_exp = x_query[train_ix[-1]].tolist()
        next_exp_2 = x_query[train_ix[-2]].tolist()

        return next_exp[0], next_exp[1], next_exp_2[0], next_exp_2[1]

    def plot_variance(self, name, num, y_var, rnd_ix, quin, test_ix):
        pointlist = np.array(
            [[quin[test_ix][i][0], quin[test_ix][i][1], y_var[i]] for i in range(len(y_var))])
        aq = plt.tricontourf(pointlist[:, 0], pointlist[:, 1], pointlist[:, 2])
        plt.colorbar(aq)
        plt.title("Next sample will be (%.2f, %.2f) with variance (%.2f)" %
                  (quin[rnd_ix][0], quin[rnd_ix][1], y_var[rnd_ix]))
        # ax.autoscale(False)
        plt.axvline(quin[rnd_ix][0], color='k')
        plt.axhline(quin[rnd_ix][1], color='k')
        plt.scatter(quin[rnd_ix][0], quin[rnd_ix][1], color='r')
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.savefig(
            f"C:/Users/SDC_1/Documents/performance/variance/variance_{name}_{num}.png")
        plt.clf()

    def plot_aqf(self, name, num, aqf, rnd_ix, quin, test_ix):
        pointlist = np.array(
            [[quin[test_ix][i][0], quin[test_ix][i][1], aqf[i]] for i in range(len(aqf))])
        aq = plt.tricontourf(pointlist[:, 0], pointlist[:, 1], pointlist[:, 2])
        plt.colorbar(aq)
        plt.title("Next sample will be (%.2f, %.2f) with acquisition of (%.2f)" % (
            quin[rnd_ix][0], quin[rnd_ix][1], aqf[rnd_ix]))
        # ax.autoscale(False)
        plt.axvline(quin[rnd_ix][0], color='k')
        plt.axhline(quin[rnd_ix][1], color='k')
        plt.scatter(quin[rnd_ix][0], quin[rnd_ix][1], color='r')
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.savefig(
            f"C:/Users/SDC_1/Documents/performance/aqf/aqf_{name}_{num}.png")
        plt.clf()

    def plot_target(self, name, num, x, y, z_con, quin, train_ix, ind=-1):
        plt.contourf(x, y, z_con)
        plt.title("Next sample will be (%.2f, %.2f)" %
                  (quin[train_ix[ind]][0], quin[train_ix[ind]][1]))
        plt.colorbar()
        plt.axvline(quin[train_ix[ind]][0], color='k')
        plt.axhline(quin[train_ix[ind]][1], color='k')
        plt.scatter(quin[train_ix[ind]][0], quin[train_ix[ind]][1], color='r')
        plt.ylabel("Y")
        plt.xlabel("X")
        plt.savefig(
            f"C:/Users/SDC_1/Documents/performance/tar/tar_{name}_{num}.png")
        plt.clf()

    # @staticmethod
    # @app.task(name='driver.ml_driver.gaussian_simulation')
    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
    def active_learning_random_forest_simulation(self, name, num, query, data, awaitedpoints):
        query = json.loads(query)
        x_query = query['x_query']
        y_query = query['y_query']
        x = [dat['x']['x'] for dat in data]
        y = [dat['x']['y'] for dat in data]
        key_x = np.array([[i, j] for i, j in zip(x, y)])
        key_y = [dat['y']['schwefel'] for dat in data]
        regr = RandomForestRegressor(n_estimators=50, random_state=1337)

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        test_ix = [i for i in range(len(x_query))]
        #train_ix = [np.random.choice(quin.shape[0], 1, replace=False)[0]]
        # we have the  first pos now (the initial point that motor goes there)
        train_ix = [np.where(x_query == j)[0][0] for j in key_x]
        #print(f"train_ix: {train_ix}")
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
        #print(f"aqf : {ix}")
        i = np.random.choice(ix)
        #print(f"chosen random : {i}")
        train_ix.append(test_ix.pop(i))
        # next position that motor needs to go
        print(f"next position is : {x_query[train_ix[-1]].tolist()}")
        next_exp = x_query[train_ix[-1]].tolist()
        #next_exp_2 = x_query[train_ix[-2]].tolist()

        #print(f"predicitons are {pred}")
        # For the sake of tracibility, we need to save the predicitons at every step
        # for i in test_ix:
        #print(f"Are you float ?! {i}")
        #prediction.update({json.dumps(x_query[{}]).format(i): pred[i]})
        return next_exp[0], next_exp[1]

    # @staticmethod
    # @app.task(name='driver.ml_driver.gaussian_simulation')

    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
    def active_learning_gaussian_simulation(self, query, data):
        # this is how the data is created in the analyis action and should be transfer here
        # data format: data={'x':{'x':d[0],'y':d[1]},'y':{'schwefel':d[2]}}
        # an example
        # data = [{'x': {'x': 1, 'y': 2}, 'y':{'schwefel': .1}}},{'x': {'x': 2, 'y': 4}, 'y':{'schwefel': .5}}}]

        #session = json.loads(session)
        # print(session)
        # print(addresses)
        # data = interpret_input(
        #    session, "session", json.loads(addresses))
        # print(data)
        query = json.loads(query)
        x_query = query['x_query']
        y_query = query['y_query']
        x = [dat['x']['x'] for dat in data]
        y = [dat['x']['y'] for dat in data]
        key_x = np.array([[i, j] for i, j in zip(x, y)])
        #key_x = [[eval(d[2])[0], eval(d[2])[1]] for d in data]
        #print(f"key_x: {key_x[0]}")
        # accumulated result at every step (n+1)
        #y_query = [d[1] for d in data]
        key_y = [dat['y']['schwefel'] for dat in data]
        #print(f"y_query: {y_query}")
        # we still need to check the format of the data
        # if x_query and y_query are string then:
        # x_query = json.loads(x_query)  # all the points of exp

        # the key_x should be in following [[4, 5], [4, 6]...]
        #key_x = np.array([[i, j] for i, j in zip(key_x['dx'], key_x['dy'])])

        # define a random forest regressor containing 50 estimators
        regr = RandomForestRegressor(n_estimators=50, random_state=1337)

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        test_ix = [i for i in range(len(x_query))]

        train_ix = [np.where(x_query == j)[0][0] for j in key_x]

        regr.fit(x_query[train_ix], y_query[train_ix])
        pred = regr.predict(x_query[test_ix])

        y_var = np.zeros([50, len(x_query[test_ix])])

        for j in range(50):
            y_var[j, :] = regr.estimators_[j].predict(x_query[test_ix])

        aqf = pred+np.var(y_var, axis=0)

        ix = np.where(aqf == np.max(aqf))[0]
        #print(f"aqf : {ix}")
        i = np.random.choice(ix)
        #print(f"chosen random : {i}")
        train_ix.append(test_ix.pop(i))
        # next position that motor needs to go
        print(f"next position is : {x_query[train_ix[-1]].tolist()}")
        next_exp = x_query[train_ix[-1]].tolist()

        return next_exp[0], next_exp[1]


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
