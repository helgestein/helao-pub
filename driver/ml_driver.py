import json

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

from celery_conf import app
from time import sleep

# for the test we just need active_learning_random_forest_simulation function


class DataUtilSim:
    def __init__(self):
        return

    # changed to the staticmethod because inside of the tasks we can't call anything from self as a DataUtilSim instance
    @staticmethod
    # name argument is required because of the project structure
    @app.task(name='machine_learning_analysis.ml_analysis.gaus_model')
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
    @app.task(name='machine_learning_analysis.ml_analysis.gaussian_simulation')
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

        model = DataUtilSim.gaus_model().fit(X, y)
        alpha = model.alpha_
        mu, var = model.predict(X, return_std=True)

        result = (alpha.tolist(), mu.tolist(), var.tolist())

        with open(save_data_path, 'w') as f:
            json.dump(result, f)

        return result

    @staticmethod
    @app.task(name='machine_learning_analysis.ml_analysis.gaussian_simulation')
    def active_learning_random_forest_simulation(key_x, key_y, x_query, y_query, save_data_path='ml_data/ml_analysis.json'):
        """[summary]

        Args:
            key_x ([type]): [the last position that machine was there]
            key_y ([type]): [the last value of schwefel function that we got]
            x_query ([type]): [list of all postions that we need to evaluate]
            y_query ([type]): [list of all calculated schwefel values according to x_query]
            save_data_path (str, optional): [description]. Defaults to 'ml_data/ml_analysis.json'.

        Returns:
            [x_suggest]: [position of the next experiment]
        """

        # we still need to check the format of the data
        # if x_query and y_query are string then:
        x_query = eval(x_query)
        y_query = eval(y_query)
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
        train_ix = [x_query.index(j) for j in key_x]
        print(train_ix)
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
        print(ix)
        i = np.random.choice(ix)
        print(i)
        train_ix.append(test_ix.pop(i))
        # next position that motor needs to go
        print(x_query[train_ix[-1]])
        next_exp = x_query[train_ix[-1]]
        prediction = pred
        return next_exp, prediction
