import numpy as np
import json
import itertools as it
import sys
if r"C:\Users\Fuzhi\Documents\GitHub\celery_task_queue" not in sys.path:
    sys.path.append(r"C:\Users\Fuzhi\Documents\GitHub\celery_task_queue")

sys.path.append(r"../driver")


class dataAnalysis:
    def __init__(self):
        self.seed = 8

    def make_grid(self, x_start, x_end, x_step, y_start, y_end, y_step, save_data_to="../data/grid.json"):
        """create a grid for the schwefel function

        Args:
            x_start ([int]): [start point in x axis]
            x_end ([int]): [end point in x axis]
            x_step ([int]): [step size for the grid along x axis]
            y_start ([int]): [start point in y axis]
            y_end ([int]): [end point in y axis]
            y_step ([int]): [step size for the grid along y axis]

        Returns:
            [type]: [list of compositions space]
        """
        x, y = [i for i in np.arange(0, 1, 0.05)], [
            i for i in np.arange(0, 1, 0.05)]

        mesh_arr = []
        for i in np.arange(x_start, x_end, x_step):
            for j in np.arange(y_start, y_end, y_step):
                mesh_arr.append([round(i, 2), round(j, 2)])
        comp = {'steps': mesh_arr}
        with open(save_data_to, 'w') as f:
            json.dump(comp, f)

        return comp

    def make_n_nary(self, n, steps, save_data_to="../data/quin.json"):
        """generate a n-nary with n number of atomic percentage

        Args:
            n ([int]): # of simplex for an arbitrary dimension
            steps ([type]): space size
            :param save_data_to: Path for the file to save data to

        Returns:
            [type]: [description]
        """
        # sleep(3)
        space_size = int(100 / (steps - 1))
        step_comb = [(i * space_size) / 100 for i in range(steps)]
        composition = [comb for comb in it.product(
            step_comb, repeat=n) if np.isclose(np.sum(comb), 1.0)]
        print("Generating a {}-ary simplex with {} entries".format(n, len(composition)))
        comp = {'steps': composition}

        with open(save_data_to, 'w') as f:
            json.dump(comp, f)

        return comp

    def schwefel_function(self, x, y):

        # you need to feed the meta[ma] in the format of string (since list is not readble by fastapi) .-> not any more 
        # upon aggrement the ma needs to change to experiment number (exp_num)
        # the save path can be changed according to what we want

        """create the Schwefel_function
        Args:
            n ([int]): # of simplex for an arbitrary dimension
            steps ([type]): space size
            vector ([string]): composition ratio for the desired material, 
            :param save_data_to: Path for the file to save data to

        Returns:
            [type]: [description]
        """
        comp = np.array([x,y])
        sch_comp = 1000 * np.array(comp) - 500
        result = 0
        for index, element in enumerate(sch_comp):
            result += - element * np.sin(np.sqrt(np.abs(element)))
        result = (-result) / 1000
        print(result)
        #with open(save_data_to, 'w') as f:
        #    json.dump(result, f)

        return result
