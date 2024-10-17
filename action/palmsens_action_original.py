from typing import Callable, Union
import sys

from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import driver.palmsens_driver
#from config import config as conf
from config.palmsens_config import config as conf
import driver.palmsens_driver as palmsens_driver

def measure(
    callback_func:Union[Callable, None],
    sampleName:str,
    method:str,
    parameters:dict,
    save_folder:str=conf["savepath_raw"]
) -> None:
    """
    This function performs a measurement in the defined method on a 
    Palmsens device. It saves the results to the path specified.

    Inputs:
    sampleName: a string defining the sample name to be used to label the sample
        for the measurement
    method: a string defining the method to be used as defined in the SDK of the
        device. Currently, this accepts "chronoamperometry" or
        "electrochemical_impedance_spectroscopy"
    parameters: a dictionary comrising the input parameters required to trigger the
        chosen method; the name of the parameter needs to be a string and be used as
        a key, while the parameter values are the values in the dictionary
    save_folder: The path to the folder, where the results shall be saved

    Outputs:
    This function has no outputs.
    """

    # Instantiate the device class, find the device and connect to it
    if callback_func is None:
        def new_data_callback(new_data):
            for type, value in new_data.items():
                print(type + ' = ' + str(value))
            return
        callback_func = new_data_callback

    Palmsens_device = palmsens_driver.PalmsensDevice(callback_func=callback_func)
    instrumentlist = Palmsens_device.find_instruments()
    Palmsens_device.connect(instrument=instrumentlist[-1])

    # Perform the measurement
    Palmsens_device.measure(
                sampleName=sampleName,
                method=method,
                parameters=parameters,
                save_folder=save_folder
                )

    # Disconnect from the device
    Palmsens_device.disconnect()


def retrieveData(
    sampleName:str,
    method:str,
    save_folder:str=conf["savepath_raw"]
) -> dict:
    ''' This function loads the data of a measurement and returns it as a dict. 
    Inputs:
    sampleName: a string defining the sample name to be used to label the sample
        for the measurement
    method: a string defining the method to be used as defined in the SDK of the
        device
    save_folder: The path to the folder, where the results shall be saved

    Outputs:
    loaded_result: the dictionary containing the results of a measruement
    '''

    loaded_result = palmsens_driver.retrieveData(sampleName=sampleName,
        method=method,
        save_folder=save_folder)

    return loaded_result