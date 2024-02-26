import pickle
from util import highestName, dict_address
from time import sleep
#from celery_conf import app
import json
import numpy as np
import pandas as pd
import math
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.ensemble import RandomForestRegressor
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import random
import sys
import matplotlib
matplotlib.use('agg')
sys.path.append(r"../")

# for the test we just need active_learning_random_forest_simulation function
kadiurl = None

class DataUtilSim:
    def __init__(self):
        return

    # changed to the staticmethod because inside of the tasks we can't call anything from self as a DataUtilSim instance
    # @staticmethod
    # name argument is required because of the project structure
    # @app.task(name='driver.ml_driver.gaus_model')

    def gaus_model(self, length_scale=1, nu_val=1.5, alpha=1e-10, constant_value = 1, noise_level = 0.1, restart_optimizer=10, random_state=42):
        """
        Define the gaussian process regressor
        :param self: instantiation
        :param length_scale: length scale
        :param restart_optimizer: number of times the optimizer restarts
        :param random_state: randomization
        :return: Gaus Model
        """
        kernel = ConstantKernel(constant_value) + Matern(length_scale=length_scale,
                            nu=nu_val) + WhiteKernel(noise_level)
        model = GaussianProcessRegressor(alpha=alpha, copy_X_train=True,
                                         kernel=kernel, n_restarts_optimizer=restart_optimizer, normalize_y=False,
                                         optimizer='fmin_l_bfgs_b', random_state=random_state)
        return model

    # changed to the staticmethod because inside of the tasks we can't call anything from self as a DataUtilSim instance
    @staticmethod
    # name argument is required because of the project structure
    #@app.task(name='driver.ml_driver.gaussian_simulation')
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
        awaitedpoints = json.loads(awaitedpoints) ## [[0.0, 12.5], [5.0, -7.5], [-7.5, 5.0]]
        awaitedpoints = [[i['x'],i['y']] for i in awaitedpoints]
        print(f"the awaiting points are {awaitedpoints}")
        query = json.loads(query)
        x_query = query["x_query"]
        y_query = query["y_query"]
        #x_query = list(filter(lambda x: x not in awaitedpoints, x_query))
        #y_query = [self.schwefel_function(x[0], x[1])for x in x_query]
        #y_query_all = query["y_query"]
        key_x = [[dat['x']['x'], dat['x']['y']] for dat in data]
        print(f"data is {data}, key_x or current points are {key_x}")
        #print(f"data is {data}, key_x or current points are {key_x} and the x query is {x_query}")
        train_ix = [x_query.index(j) for j in key_x] # only data from current experiment or all measured data?!
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


        #print(f"the train indices are {train_ix} and the train data are {x_query[train_ix]} and test indices are {test_ix}")

        regr.fit(x_query[train_ix], y_query[train_ix])
        pred = regr.predict(x_query[test_ix])
        #print(pred)
        y_var_ = np.zeros([50, len(x_query[test_ix])])

        for j in range(50):
            y_var_[j, :] = regr.estimators_[j].predict(x_query[test_ix])

        y_var = np.var(y_var_, axis=0)
        aqf = pred+y_var

        ix = np.where(aqf == np.max(aqf))[0]
        #print(f"aqf : {ix}")
        i = np.random.choice(ix)
        #####print(f"indeces for the next experiment are {i}")
        print(f"indices for the next experiment are {test_ix[i]}")
        print(f"train indices before popping {train_ix}")

        #x_grid, y_grid = np.meshgrid(
        #    [2.5 * i for i in range(21)], [2.5 * i for i in range(21)])
        #schwefel_grid = np.array(y_query_all).reshape(21, 21)
        #x_grid, y_grid = np.meshgrid(np.arange(-25, 27.5, 2.5),np.arange(-25, 27.5, 2.5))
        #z_grid = np.array(y_query).reshape(21, 21)
        
        self.plot_aqf(name, num, aqf, i, x_query, test_ix, train_ix)
        self.plot_variance(name, num, y_var, i, x_query, test_ix, train_ix)
        self.plot_prediction(name, num, pred, i, x_query, y_query, test_ix, train_ix)
        self.plot_target_wafer(name, num, x_query, y_query, i, test_ix, train_ix)
        #self.plot_target(name, num, x_grid, y_grid, z_grid, x_query, i, test_ix) # if standard grid is used

        train_ix.append(test_ix.pop(i)) ### seems to be correct
        next_exp = x_query[train_ix[-1]].tolist()
        print(f"next first position is : {next_exp}")
        #self.plot_target(name, num, x_grid, y_grid, z_grid, x_query, train_ix, ind=-1)
        return next_exp[0], next_exp[1]

    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
    
    def active_learning_gaussian_simulation_parallel(self, name, num, query, data, awaitedpoints, exp_exl_ratio):
        
        random.seed(42)
        awaitedpoints = json.loads(awaitedpoints)
        awaitedpoints = [[i['x'],i['y']] for i in awaitedpoints]
        print(f"the awaiting points are {awaitedpoints}")
        query = json.loads(query)
        x_query = query['x_query']
        y_query = query['y_query'] 
        key_x = [[dat['x']['x'], dat['x']['y']] for dat in data]
        print(f"data is {data}, key_x or current points are {key_x}")
        train_ix = [x_query.index(j) for j in key_x]
        test_ix = [x_query.index(i) for i in x_query if i not in key_x and i not in awaitedpoints]

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query) 
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        regr = self.gaus_model()
        #regr.fit(x_query[train_ix], y_query[train_ix])
        regr.fit(C[train_ix], y_query[train_ix])

        #y_mean, y_var = regr.predict(x_query[test_ix], return_std=True)
        y_mean, y_var = regr.predict(C[test_ix], return_std=True)
        aqf = exp_exl_ratio * y_mean + (1 - exp_exl_ratio) * y_var

        ix = np.where(aqf == np.max(aqf))[0]
        i = np.random.choice(ix)
        
        print(f"indices for the next experiment are {test_ix[i]}")
        print(f"train indices before popping {train_ix}")
        
        self.plot_aqf(name, num, aqf, i, x_query, test_ix, train_ix)
        self.plot_variance(name, num, y_var, i, x_query, test_ix, train_ix)
        self.plot_prediction(name, num, y_mean, i, x_query, y_query, test_ix, train_ix)
        self.plot_target_wafer(name, num, x_query, y_query, i, test_ix, train_ix)

        #self.plot_aqf("sdc_2_{}".format(num) , aqf, i[1], x_query, test_ix)
        #self.plot_variance("sdc_2_{}".format(num), y_var, i[1], x_query, test_ix)

        #self.plot_target("sdc_2_{}".format(num), x_grid, y_grid, z_con, x_query, train_ix, ind=-2)

        # next position that motor needs to go
        train_ix.append(test_ix.pop(i)) ### seems to be correct
        next_exp = x_query[train_ix[-1]].tolist()
        print(f"next first position is : {next_exp}")
        print(f"train indices after popping {train_ix}")

        return next_exp[0], next_exp[1]

    def active_learning_gaussian_simulation_parallel_wafer(self, name, num, query, data, awaitedpoints, exp_exl_ratio):
        
        random.seed(1)
        awaitedpoints = json.loads(awaitedpoints) ## [[0.0, 12.5], [5.0, -7.5], [-7.5, 5.0]]
        awaitedpoints = [[i['x'], i['y']] for i in awaitedpoints]
        print(f"the awaiting points are {awaitedpoints}")
        query = json.loads(query)
        x_query = query["x_query"]
        c_query = query['c_query']
        q_query = query['q_query']
        i_query = query['i_query']
        key_x = [[dat['X']['x'], dat['X']['y']] for dat in data]
        key_y = [dat['Y']['Q3']/1000 for dat in data]
        print(f"data is {data}, key_x or current points are {key_x}, key_y are {key_y}")
        train_ix = [x_query.index(j) for j in key_x] # only data from current experiment or all measured data?!
        test_ix = [x_query.index(i) for i in x_query if i not in key_x and i not in awaitedpoints]

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(c_query) != np.ndarray:
            c_query = np.array(c_query)
        if type(q_query) != np.ndarray:
            q_query = np.array(q_query)
        if type(i_query) != np.ndarray:
            i_query = np.array(i_query)

        # test_ix = [i for i in range(len(x_query))]
        # print(f"test indeces are {test_ix}")
        # train_ix = [np.where(x_query == j)[0] for j in key_x]
        # print(f"the train indeces are {train_ix}  and the train data are {x_query[train_ix]}")
        print('Capacity measured:', key_y[-1]*1000)
        print('Capacity expected:', q_query[train_ix][-1])

        for i in range(len(key_y) - 1, -1, -1):
            if 1000 * key_y[i] < 0.25 * q_query[train_ix][i] or 1000 * key_y[i] > 1.25 * q_query[train_ix][i]:
                del key_y[i]
                del train_ix[i]

        #print(f"the train indices are {train_ix} and the train data are {x_query[train_ix]} and test indices are {test_ix}")
        print('Training data', c_query[train_ix], key_y)
        print('Testing data', c_query[test_ix])
        regr = self.gaus_model()
        #regr.fit(x_query[train_ix], y_query[train_ix])
        regr.fit(c_query[train_ix], key_y)

        #y_mean, y_var = regr.predict(x_query[test_ix], return_std=True)
        y_mean, y_var = regr.predict(c_query[test_ix], return_std=True)
        y_mean, y_var = 1000*y_mean, 1000*y_var
        aqf = (1 - exp_exl_ratio) * y_mean + exp_exl_ratio * y_var
        
        print('y_mean', y_mean)
        print('aqf', aqf)
        if len(train_ix) == 1:
            i = random.choice(test_ix)
        else:
            ix = np.where(aqf == np.max(aqf))[0]
            i = np.random.choice(ix)
            print("ids max aqf", ix)

        #####print(f"indeces for the next experiment are {i}")
        print(f"indices for the next experiment are {test_ix[i]}")
        print(f"train indices before popping {train_ix}")

        #x_grid, y_grid = np.meshgrid(
        #    [2.5 * i for i in range(21)], [2.5 * i for i in range(21)])
        #schwefel_grid = np.array(y_query_all).reshape(21, 21)
        #x_grid, y_grid = np.meshgrid(np.arange(-25, 27.5, 2.5),np.arange(-25, 27.5, 2.5))
        #z_grid = np.array(y_query).reshape(21, 21)
        
        self.plot_aqf(name, num, aqf, i, x_query, test_ix, train_ix)
        self.plot_variance(name, num, y_var, i, x_query, test_ix, train_ix)
        self.plot_prediction(name, num, y_mean, i, x_query, [1000*i for i in key_y], test_ix, train_ix)
        #self.plot_prediction(name, num, y_mean, i, x_query, y_query, test_ix, train_ix) # when y values are known in advance
        self.plot_target_wafer(name, num, x_query, q_query, i, test_ix, train_ix)
        #self.plot_target_wafer(name, num, x_query, y_query, i, test_ix, train_ix) # when y values are known in advance
        #self.plot_target(name, num, x_grid, y_grid, z_grid, x_query, i, test_ix) # if standard grid is used

        ternary_plot = TernaryPlot(labels=('Si', 'Ge', 'Sn'))
        ternary_plot.plot(c_query[train_ix], [1000*i for i in key_y], name, num)

        train_ix.append(test_ix.pop(i)) ### seems to be correct
        next_exp = x_query[train_ix[-1]].tolist()
        next_cur = i_query[train_ix[-1]].tolist() # correct for real exp
        #next_cur = 0.001*q_query[train_ix[-1]].tolist() # correct for real exp
        print(f"next first position is : {next_exp}, next current is {next_cur}")
        #self.plot_target(name, num, x_grid, y_grid, z_grid, x_query, train_ix, ind=-1)
        return next_exp[0], next_exp[1], next_cur

    def active_learning_random_forest_simulation_parallel_wafer(self, name, num, query, data, awaitedpoints, exp_exl_ratio):
        
        random.seed(11)
        awaitedpoints = json.loads(awaitedpoints) ## [[0.0, 12.5], [5.0, -7.5], [-7.5, 5.0]]
        awaitedpoints = [[i['x'], i['y']] for i in awaitedpoints]
        print(f"the awaiting points are {awaitedpoints}")
        query = json.loads(query)
        x_query = query["x_query"]
        c_query = query['c_query']
        q_query = query['q_query']
        i_query = query['i_query']
        key_x = [[dat['X']['x'], dat['X']['y']] for dat in data]
        key_y = [dat['Y']['Q']/1 for dat in data]
        print(f"data is {data}, key_x or current points are {key_x}, key_y are {key_y}")
        train_ix = [x_query.index(j) for j in key_x] # only data from current experiment or all measured data?!
        test_ix = [x_query.index(i) for i in x_query if i not in key_x and i not in awaitedpoints]

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(c_query) != np.ndarray:
            c_query = np.array(c_query)
        if type(q_query) != np.ndarray:
            q_query = np.array(q_query)
        if type(i_query) != np.ndarray:
            i_query = np.array(i_query)

        # test_ix = [i for i in range(len(x_query))]
        # print(f"test indeces are {test_ix}")
        # train_ix = [np.where(x_query == j)[0] for j in key_x]
        # print(f"the train indeces are {train_ix}  and the train data are {x_query[train_ix]}")

        #print(f"the train indices are {train_ix} and the train data are {x_query[train_ix]} and test indices are {test_ix}")
        print('Training data', c_query[train_ix], key_y)
        print('Testing data', c_query[test_ix])

        regr = RandomForestRegressor(n_estimators=50, random_state=36)

        regr.fit(c_query[train_ix], key_y)
        y_mean = regr.predict(c_query[test_ix])
        y_mean = y_mean*1000

        y_var_ = np.zeros([50, len(x_query[test_ix])])
        for j in range(50):
            y_var_[j, :] = regr.estimators_[j].predict(c_query[test_ix])

        y_var = np.var(y_var_, axis=0) * 1
        aqf = exp_exl_ratio * y_mean + (1 - exp_exl_ratio) * y_var
        
        print('y_mean', y_mean)
        print('aqf', aqf)
        ix = np.where(aqf == np.max(aqf))[0]
        print("ids", ix)
        i = np.random.choice(ix)

        #####print(f"indeces for the next experiment are {i}")
        print(f"indices for the next experiment are {test_ix[i]}")
        print(f"train indices before popping {train_ix}")

        #x_grid, y_grid = np.meshgrid(
        #    [2.5 * i for i in range(21)], [2.5 * i for i in range(21)])
        #schwefel_grid = np.array(y_query_all).reshape(21, 21)
        #x_grid, y_grid = np.meshgrid(np.arange(-25, 27.5, 2.5),np.arange(-25, 27.5, 2.5))
        #z_grid = np.array(y_query).reshape(21, 21)
        
        self.plot_aqf(name, num, aqf, i, x_query, test_ix, train_ix)
        self.plot_variance(name, num, y_var, i, x_query, test_ix, train_ix)
        #self.plot_prediction(name, num, y_mean, i, x_query, key_y, test_ix, train_ix)
        self.plot_prediction(name, num, y_mean, i, x_query, [1000*i for i in key_y], test_ix, train_ix)
        #self.plot_prediction(name, num, y_mean, i, x_query, y_query, test_ix, train_ix) # when y values are known in advance
        self.plot_target_wafer(name, num, x_query, q_query, i, test_ix, train_ix)
        #self.plot_target_wafer(name, num, x_query, y_query, i, test_ix, train_ix) # when y values are known in advance
        #self.plot_target(name, num, x_grid, y_grid, z_grid, x_query, i, test_ix) # if standard grid is used

        ternary_plot = TernaryPlot(labels=('Si', 'Ge', 'Sn'))
        ternary_plot.plot(c_query[train_ix], [1*i for i in key_y], name, num)

        train_ix.append(test_ix.pop(i)) ### seems to be correct
        next_exp = x_query[train_ix[-1]].tolist()
        #next_cur = i_query[train_ix[-1]].tolist() # correct for real exp
        next_cur = 0.001*q_query[train_ix[-1]].tolist() # correct for real exp
        print(f"next first position is : {next_exp}, next current is {next_cur}")
        #self.plot_target(name, num, x_grid, y_grid, z_grid, x_query, train_ix, ind=-1)
        return next_exp[0], next_exp[1], next_cur
    
    '''def active_learning_gaussian_simulation_parallel(self, name, num, query, data, exp_exl_ratio=0.4):

        query = json.loads(query)
    
        x_query = query['x_query']
        y_query = query['y_query'] 
        print("DATA", data)
        x = [dat['x']['x'] for dat in data] 
        y = [dat['x']['y'] for dat in data] 
        key_x = np.array([[i, j] for i, j in zip(x, y)]) 
        print("x,y,key_x", x, y, key_x)
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

        return next_exp[0], next_exp[1], next_exp_2[0], next_exp_2[1]'''

    def transformations(self):
        df = pd.read_csv(r'C:\Users\LaborRatte23-2\Documents\SDC functions\Python scripts\df_lim.csv').to_numpy()
        XY, C, I, Q = df[:,0:2], df[:,2:5], df[:,-2], df[:,-1]
        return XY, C, I, Q
    
    def plot_variance(self, name, num, y_var, rnd_ix, quin, test_ix, train_ix):
        plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
        plt.rcParams["axes.labelweight"] = "bold"
        plt.subplots(dpi=100)
        #pointlist = np.array(
        #    [[quin[test_ix][i][0], quin[test_ix][i][1], y_var[i]] for i in range(len(y_var))])
        pointlist = np.array(
            [[-quin[test_ix][i][0]-16.25, quin[test_ix][i][1]-48.15, y_var[i]] for i in range(len(y_var))])
        aq = plt.tricontourf(pointlist[:, 0], pointlist[:, 1], pointlist[:, 2], levels=25, cmap = plt.cm.viridis)
        plt.colorbar(aq)
        #plt.title("Next sample will be (%.2f, %.2f) with variance (%.2f)" %
        #          (quin[test_ix][rnd_ix][0], quin[test_ix][rnd_ix][1], y_var[rnd_ix]), y=1.04)
        plt.title("Next sample will be (%.2f, %.2f) with variance (%.2f)" %
                  (-quin[test_ix][rnd_ix][0]-16.25, quin[test_ix][rnd_ix][1]-48.15, y_var[rnd_ix]), y=1.04)
        # ax.autoscale(False)
        #plt.axvline(quin[test_ix][rnd_ix][0], color='k')
        plt.axvline(-quin[test_ix][rnd_ix][0]-16.25, color='k')
        #plt.axhline(quin[test_ix][rnd_ix][1], color='k')
        plt.axhline(quin[test_ix][rnd_ix][1]-48.15, color='k')
        #plt.scatter(quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1], color='r', label = 'Next sample')
        plt.scatter(-quin[test_ix[rnd_ix]][0]-16.25, quin[test_ix[rnd_ix]][1]-48.15, color='r', label = 'Next sample')
        #plt.scatter(quin[train_ix][:,0], quin[train_ix][:,1], color='k', label = 'Measured points')
        plt.scatter(-quin[train_ix][:,0]-16.25, quin[train_ix][:,1]-48.15, color='k', label = 'Measured points')
        plt.xlabel("X, mm")
        plt.ylabel("Y, mm")
        plt.savefig(
            f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/AL/var/var_{name}_{num}.png", transparent=False)
        plt.clf()
        plt.close('all')

    def plot_aqf(self, name, num, aqf, rnd_ix, quin, test_ix, train_ix):
        plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
        plt.rcParams["axes.labelweight"] = "bold"
        plt.subplots(dpi=100)
        #pointlist = np.array(
        #    [[quin[test_ix][i][0], quin[test_ix][i][1], aqf[i]] for i in range(len(aqf))])
        pointlist = np.array(
            [[-quin[test_ix][i][0]-16.25, quin[test_ix][i][1]-48.15, aqf[i]] for i in range(len(aqf))])
        aq = plt.tricontourf(pointlist[:, 0], pointlist[:, 1], pointlist[:, 2], levels=25, cmap = plt.cm.viridis)
        plt.colorbar(aq)
        #plt.title("Next sample will be (%.2f, %.2f) with acquisition of (%.2f)" % (
        #    quin[test_ix][rnd_ix][0], quin[test_ix][rnd_ix][1], aqf[rnd_ix]), y=1.04)
        plt.title("Next sample will be (%.2f, %.2f) with acquisition of (%.2f)" % (
            -quin[test_ix][rnd_ix][0]-16.25, quin[test_ix][rnd_ix][1]-48.15, aqf[rnd_ix]), y=1.04)
        # ax.autoscale(False)
        #plt.axvline(quin[test_ix][rnd_ix][0], color='k')
        plt.axvline(-quin[test_ix][rnd_ix][0]-16.25, color='k')
        #plt.axhline(quin[test_ix][rnd_ix][1], color='k')
        plt.axhline(quin[test_ix][rnd_ix][1]-48.15, color='k')
        #plt.scatter(quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1], color='r', label = 'Next sample')
        plt.scatter(-quin[test_ix[rnd_ix]][0]-16.25, quin[test_ix[rnd_ix]][1]-48.15, color='r', label = 'Next sample')
        #plt.scatter(quin[train_ix][:,0], quin[train_ix][:,1], color='k', label = 'Measured points')
        plt.scatter(-quin[train_ix][:,0]-16.25, quin[train_ix][:,1]-48.15, color='k', label = 'Measured points')
        plt.xlabel("X, mm")
        plt.ylabel("Y, mm")
        plt.savefig(
            f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/AL/aqf/aqf_{name}_{num}.png", transparent=False)
        plt.clf()
        plt.close('all')

    #def plot_target(self, name, num, x, y, z_con, quin, train_ix, ind=-1):
    def plot_target(self, name, num, x, y, z_con, quin, rnd_ix, test_ix, train_ix):
        plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
        plt.rcParams["axes.labelweight"] = "bold"
        plt.subplots(dpi=100)
        plt.contourf(x, y, z_con, levels=25, cmap = plt.cm.viridis)
        #plt.title("Next sample will be (%.2f, %.2f)" %
        #          (quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1]), y=1.04)
        plt.title("Next sample will be (%.2f, %.2f)" %
                  (-quin[test_ix[rnd_ix]][0]-16.25, quin[test_ix[rnd_ix]][1]-48.15), y=1.04)
        plt.colorbar()
        #plt.axvline(quin[test_ix[rnd_ix]][0], color='k')
        plt.axvline(-quin[test_ix[rnd_ix]][0]-16.25, color='k')
        #plt.axhline(quin[test_ix[rnd_ix]][1], color='k')
        plt.axhline(quin[test_ix[rnd_ix]][1]-48.15, color='k')
        #plt.scatter(quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1], color='r', label = 'Next sample')
        plt.scatter(-quin[test_ix[rnd_ix]][0]-16.25, quin[test_ix[rnd_ix]][1]-48.15, color='r', label = 'Next sample')
        #plt.scatter(quin[train_ix][:,0], quin[train_ix][:,1], color='k', label = 'Measured points')
        plt.scatter(-quin[train_ix][:,0]-16.25, quin[train_ix][:,1]-48.15, color='k', label = 'Measured points')
        plt.ylabel("Y, mm")
        plt.xlabel("X, mm")
        plt.savefig(
            f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/AL/tar/tar_{name}_{num}.png", transparent=False)
        plt.clf()
        plt.close('all')

    def plot_target_wafer(self, name, num, quin, y_query, rnd_ix, test_ix, train_ix):
        plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
        plt.rcParams["axes.labelweight"] = "bold"
        plt.subplots(dpi=100)
        #xi = np.linspace(min(quin[:,0]), max(quin[:,0]), 1000)
        xi = np.linspace(min(-quin[:,0]-16.25), max(-quin[:,0]-16.25), 1000)
        #yi = np.linspace(min(quin[:,1]), max(quin[:,1]), 1000)
        yi = np.linspace(min(quin[:,1]-48.15), max(quin[:,1]-48.15), 1000)
        xi, yi = np.meshgrid(xi, yi)
        #zi = griddata((quin[:,0], quin[:,1]), y_query, (xi, yi), method='linear')
        zi = griddata((-quin[:,0]-16.25, quin[:,1]-48.15), y_query, (xi, yi), method='linear')
        plt.contourf(xi, yi, zi, levels=25, cmap = plt.cm.viridis)
        #plt.title("Next sample will be (%.2f, %.2f)" %
        #          (quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1]), y=1.04)
        plt.title("Next sample will be (%.2f, %.2f)" %
                  (quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1]), y=1.04)
        plt.colorbar()
        #plt.axvline(quin[test_ix[rnd_ix]][0], color='k')
        plt.axvline(-quin[test_ix[rnd_ix]][0]-16.25, color='k')
        #plt.axhline(quin[test_ix[rnd_ix]][1], color='k')
        plt.axhline(quin[test_ix[rnd_ix]][1]-48.15, color='k')
        #plt.scatter(quin[test_ix[rnd_ix]][0], quin[test_ix[rnd_ix]][1], color='r', label = 'Next sample')
        plt.scatter(-quin[test_ix[rnd_ix]][0]-16.25, quin[test_ix[rnd_ix]][1]-48.15, color='r', label = 'Next sample')
        #plt.scatter(quin[train_ix][:,0], quin[train_ix][:,1], color='k', label = 'Measured points')
        plt.scatter(-quin[train_ix][:,0]-16.25, quin[train_ix][:,1]-48.15, color='k', label = 'Measured points')
        plt.ylabel("Y, mm")
        plt.xlabel("X, mm")
        plt.savefig(
            f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/AL/tar/tar_{name}_{num}.png", transparent=False)
        plt.clf()
        plt.close('all')

    def plot_prediction(self, name, num, pred, rnd_ix, quin, y_query, test_ix, train_ix):
        plt.rcParams.update({'font.size': 12, 'font.family': 'Arial'}) # general parameters
        plt.rcParams["axes.labelweight"] = "bold"
        plt.subplots(dpi=100)
        #pointlist = np.array(
        #    [[quin[test_ix][i][0], quin[test_ix][i][1], pred[i]] for i in range(len(pred))])
        pointlist = np.array(
            [[-quin[test_ix][i][0]-16.25, quin[test_ix][i][1]-48.15, pred[i]] for i in range(len(pred))])
        aq = plt.tricontourf(pointlist[:, 0], pointlist[:, 1], pointlist[:, 2], levels=25, cmap = plt.cm.viridis)
        plt.colorbar(aq)
        #plt.title("Next sample will be (%.2f, %.2f) with prediction (%.2f)" %
        #          (quin[test_ix][rnd_ix][0], quin[test_ix][rnd_ix][1], pred[rnd_ix]), y=1.04)
        plt.title("Next sample will be (%.2f, %.2f) with prediction (%.2f)" %
                  (-quin[test_ix][rnd_ix][0]-16.25, quin[test_ix][rnd_ix][1]-48.15, pred[rnd_ix]), y=1.04)
        # ax.autoscale(False)
        #plt.axvline(quin[test_ix][rnd_ix][0], color='k')
        plt.axvline(-quin[test_ix][rnd_ix][0]-16.25, color='k')
        #plt.axhline(quin[test_ix][rnd_ix][1], color='k')
        plt.axhline(quin[test_ix][rnd_ix][1]-48.15, color='k')
        #plt.scatter(quin[test_ix][rnd_ix][0], quin[test_ix][rnd_ix][1], color='r', label = 'Next sample')
        plt.scatter(-quin[test_ix][rnd_ix][0]-16.25, quin[test_ix][rnd_ix][1]-48.15, color='r', label = 'Next sample')
        #plt.scatter(quin[train_ix][:,0], quin[train_ix][:,1], c=y_query[train_ix], label = 'Measured points') # when all the values are known
        plt.scatter(-quin[train_ix][:,0]-16.25, quin[train_ix][:,1]-48.15, c=y_query, label = 'Measured points')
        plt.xlabel("X, mm")
        plt.ylabel("Y, mm")
        plt.savefig(
            f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/AL/pred/pred_{name}_{num}.png", transparent=False)
        plt.clf()
        plt.close('all')

    # @staticmethod
    # @app.task(name='driver.ml_driver.gaussian_simulation')
    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])

    '''def active_learning_random_forest_simulation(self, name, num, query, data, awaitedpoints):
        query = json.loads(query)
        awaitedpoints = json.loads(awaitedpoints)
        awaitedpoints = [[i['x'],i['y']] for i in awaitedpoints]
        print(f"the awaiting points are {awaitedpoints}")
        x_query = query['x_query'] # list of all coordinates [[x,y]]
        y_query = [self.schwefel_function(x[0], x[1])for x in x_query]
        #y_query = query['y_query'] # list of all z-values (schwefel)
        #x = [dat['x']['x'] for dat in data] # list of x coordinates (measured)
        #y = [dat['x']['y'] for dat in data] # list of y coordinates (measured)
        #key_x = np.array([[i, j] for i, j in zip(x, y)]) # array of [[x,y]] coordinates
        key_x = [[dat['x']['x'], dat['x']['y']] for dat in data]
        print(f"data is {data}, key_x or current points are {key_x} and the x query is {x_query}")
        #key_y = [dat['y']['schwefel'] for dat in data] # list of z-values measured

        if type(x_query) != np.ndarray:
            x_query = np.array(x_query)
        if type(y_query) != np.ndarray:
            y_query = np.array(y_query)

        train_ix = [x_query.index(j) for j in key_x]
        test_ix = [x_query.index(i) for i in x_query if i not in key_x and i not in awaitedpoints]
        print(f"the train indices are {train_ix} and the train data are {x_query[train_ix]}and test indices are {test_ix}")
        #test_ix = [i for i in range(len(x_query))] # list of ids of [x,y]
        #train_ix = [np.random.choice(quin.shape[0], 1, replace=False)[0]]
        # we have the  first pos now (the initial point that motor goes there)
        #train_ix = [np.where(x_query == j)[0][0] for j in key_x]  # list of ids of [x,y] measured
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
        regr = RandomForestRegressor(n_estimators=50, random_state=1337) # regressor
        regr.fit(x_query[train_ix], y_query[train_ix])
        pred = regr.predict(x_query[test_ix])

        y_var = np.zeros([50, len(x_query[test_ix])])

        for j in range(50):
            y_var[j, :] = regr.estimators_[j].predict(x_query[test_ix])

        aqf = pred+np.var(y_var, axis=0) # alpha should be added

        ix = np.where(aqf == np.max(aqf))[0]
        print(f"aqf : {ix}")
        i = np.random.choice(ix)
        print(f"chosen random : {i}")
        train_ix.append(test_ix.pop(i))
        print(f"Train indices are {train_ix}")
        # next position that motor needs to go
        print(f"indices for the next experiment are {i}")
        print(f"next position is : {x_query[train_ix[-1]].tolist()}")
        next_exp = x_query[train_ix[-1]].tolist()
        print(f"next first position is : {next_exp}")
        #next_exp_2 = x_query[train_ix[-2]].tolist()
        #print(f"predicitons are {pred}")
        # For the sake of tracibility, we need to save the predicitons at every step
        # for i in test_ix:
        #print(f"Are you float ?! {i}")
        #prediction.update({json.dumps(x_query[{}]).format(i): pred[i]})
        return next_exp[0], next_exp[1]'''

    # @staticmethod
    # @app.task(name='driver.ml_driver.gaussian_simulation')

    # , addresses="schwefelFunction/data/key_y"): #json.dumps(["moveSample/parameters", "schwefel_function/data/key_y"])
    '''def active_learning_gaussian_simulation(self, query, data):
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

        return next_exp[0], next_exp[1]'''


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

class TernaryPlot:
    def __init__(self, labels=('C1', 'C2', 'C3'), font = {'fontname':'Arial'}):
        """
        Initialize the TernaryPlot object with customizable options.
        :param labels: Labels for the ternary components.
        """
        self.labels = labels
        self.font = font
    def to_cartesian(self, tern):
        """
        Convert ternary coordinates to Cartesian coordinates.
        :param tern: Array of ternary coordinates.
        :return: Cartesian coordinates as (x, y).
        """
        cart_xs = 1. - tern[:, 0] - tern[:, 1] / 2.
        cart_ys = np.sqrt(3) * tern[:, 1] / 2.0
        return cart_xs, cart_ys
    def _rot(self):
        angle = math.radians(60)
        inv = np.matrix([[1,0],[0,-1]])
        def rot (alpha):
            rot = np.matrix([[np.cos(alpha),-np.sin(alpha)],
                            [np.sin(alpha),np.cos(alpha)]])
            return rot
        tr = rot(math.radians(60))*inv*rot(math.radians(60)).T
        return angle, tr, rot
    def _pos_ticks(self):
        angle, tr, rot = self._rot()
        '''axis ticks positions (L = large and s = small)'''
        tick0 = np.array([[i/10,0] for i in range (int(11))])
        tick0L = np.array([[-1/40*math.cos(math.pi/3)+i/10,-1/40*math.sin(math.pi/3)] for i in range (11)])
        tick0s = np.array([[-1/40/2*math.cos(math.pi/3)+i/10,-1/40/2*math.sin(math.pi/3)] for i in range (11)])
        tick1 = (tr*(rot(angle)*tick0.T)).T
        tick1L = (rot(angle)*(np.array([[1/40*math.cos(math.pi/3)+i/10,1/40*math.sin(math.pi/3)] for i in range (11)])).T).T
        tick1s = (rot(angle)*(np.array([[1/40/2*math.cos(math.pi/3)+i/10,1/40/2*math.sin(math.pi/3)] for i in range (11)])).T).T
        tick2 = (np.matrix([[-1,0],[0,1]])*((tr*(rot(angle)*tick0.T)).T-np.array([0.5,0])).T).T+np.array([0.5,0])
        tick2L = (np.matrix([[-1,0],[0,1]])*((tr*(rot(angle)*tick0L.T)).T-np.array([0.5,0])).T).T+np.array([0.5,0])
        tick2s = (np.matrix([[-1,0],[0,1]])*((tr*(rot(angle)*tick0s.T)).T-np.array([0.5,0])).T).T+np.array([0.5,0])
        return tick0, tick0L, tick0s, tick1, tick1L, tick1s, tick2, tick2L, tick2s
    def _pos_axis(self):    
        text0 = np.array([[-1/15*math.cos(math.pi/3)+i/5,-1/15*math.sin(math.pi/3)] for i in range (6)])
        text1 = np.array([[(-1/15+i/5)*math.cos(math.pi/3),+(1/15+i/5)*math.sin(math.pi/3)] for i in range (6)])
        text2 = np.array([[1+1/15-i/5*math.cos(math.pi/3),i/5*math.sin(math.pi/3)] for i in range (6)])
        return text0, text1, text2
    def _add_labels(self):
        """Add labels to the plot"""
        labels = self.labels
        a_shift = 1/8
        d_shift = 1/30
        angle_shift = math.pi/6
        labels_shift = [[-a_shift*math.cos(angle_shift),-a_shift*math.sin(angle_shift)],[0.5,np.sqrt(3)/2+a_shift],[1+a_shift*math.cos(angle_shift),-a_shift*math.sin(angle_shift)]]
        labels_rot = [-60, 0 ,60]
        font = self.font
        for i in range(3):
            plt.text(labels_shift[i][0],labels_shift[i][1],s=labels[i],fontsize=18,weight='bold',**font,rotation=labels_rot[i],horizontalalignment='center',verticalalignment='center')
    def _add_ticks(self):
        """Enhanced method to add customizable ticks to the plot"""
        tick0, tick0L, tick0s, tick1, tick1L, tick1s, tick2, tick2L, tick2s = self._pos_ticks()
        loop_range = tick0.shape[0] // 2
        """Large ticks"""
        for i in range(loop_range+1):
            plt.plot([tick0[2*i,0], tick0L[2*i,0]], [tick0[2*i,1], tick0L[2*i,1]], color='black', linewidth=1.5, zorder=90)
            plt.plot([tick1[2*i,0], tick1L[2*i,0]], [tick1[2*i,1], tick1L[2*i,1]], color='black', linewidth=1.5, zorder=90)
            plt.plot([tick2[2*i,0], tick2L[2*i,0]], [tick2[2*i,1], tick2L[2*i,1]], color='black', linewidth=1.5, zorder=90)
        """Small ticks"""
        for i in range(loop_range):
            plt.plot([tick0[2*i+1,0], tick0s[2*i+1,0]], [tick0[2*i+1,1], tick0s[2*i+1,1]], color='black', linewidth=1.5)
            plt.plot([tick1[2*i+1,0], tick1s[2*i+1,0]], [tick1[2*i+1,1], tick1s[2*i+1,1]], color='black', linewidth=1.5)
            plt.plot([tick2[2*i+1,0], tick2s[2*i+1,0]], [tick2[2*i+1,1], tick2s[2*i+1,1]], color='black', linewidth=1.5)
    def _add_ticks_labels(self):
        """Add ticks labels"""
        text0, text1, text2 = self._pos_axis()
        for i in range(text0.shape[0]):
            font = self.font
            plt.text(text0[i,0],text0[i,1],s=round(i/5,1),fontsize=12,**font,rotation=60,horizontalalignment='center',verticalalignment='center')
            plt.text(text1[i,0],text1[i,1],s=round(1-i/5,1),fontsize=12,**font,rotation=-60,horizontalalignment='center',verticalalignment='center')
            plt.text(text2[i,0],text2[i,1],s=round(i/5,1),fontsize=12,**font,rotation=0,horizontalalignment='center',verticalalignment='center')
    def _add_triangle(self):
        """Draw the grid lines of the ternary triangle."""
        tick0, tick0L, tick0s, tick1, tick1L, tick1s, tick2, tick2L, tick2s = self._pos_ticks()
        for i in range(tick0.shape[0]-2):
            plt.plot([tick0[i+1,0],tick1[i+1,0]],[tick0[i+1,1],tick1[i+1,1]],color='gray',linestyle='dashed',linewidth=1.5,alpha=0.5)
            plt.plot([tick1[i+1,0],tick2[i+1,0]],[tick1[i+1,1],tick2[i+1,1]],color='gray',linestyle='dashed',linewidth=1.5,alpha=0.5)
            plt.plot([tick2[i+1,0],tick0[tick0.shape[0]-2-i,0]],[tick2[i+1,1],tick0[tick0.shape[0]-2-i,1]],color='gray',linestyle='dashed',linewidth=1.5,alpha=0.5)
        """Draw the lines of the ternary triangle."""
        lines = [[0,0],[0.5,np.sqrt(3)/2],[1,0]]
        for i in [[0,1],[1,2],[2,0]]:
            plt.plot([lines[i[0]][0],lines[i[1]][0]],[lines[i[0]][1],lines[i[1]][1]],color='black',linewidth=2.5, zorder=100)
    def plot(self, data, Y, name, num):
        """
        Plot ternary diagram with given data.
        :param data: Array of ternary coordinates.
        """
        cart_xs, cart_ys = self.to_cartesian(data)
        fig, ax = plt.subplots(dpi=100)
        im = plt.scatter(cart_xs,cart_ys,c=Y,s=25,marker="h",zorder=10,alpha=1,cmap=plt.cm.jet)
        cbar = fig.colorbar(im, label='Specific capacity, mAh/g', ax=ax, pad=0, shrink=1, format='%.0f')
        cbar.ax.set_position([0.84, 0.15, 0.05, 0.75])
        self._add_ticks()
        self._add_labels()
        self._add_ticks_labels()
        self._add_triangle()
        plt.axis('equal')
        plt.axis('off')
        fig.patch.set_facecolor('white')
        plt.savefig(
            f"C:/Users/LaborRatte23-2/Documents/data/substrate_109/AL/ter/ter_{name}_{num}.png", transparent=False)
        plt.clf()
        plt.close('all')
