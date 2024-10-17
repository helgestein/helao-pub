from pathlib import Path
import json
from typing import Any
import sys
from importlib import import_module
from datetime import datetime

def default_converter(o):
    if isinstance(o, datetime):
        return o.__str__()

def saveToFile(folder:str, filename:str, extension:str, data:str) -> None:
    ''' This function saves an object passed as data to a .txt file in the path given in savePath. The savePath must include
    the filename and the extension .txt
    
    Inputs:
    folder: a string specifying the path to the folder, to which the data shall be saved
    filename: a string specifying the filename of the output file
    data: a string representing the data to be saved in the .txt file
    
    Outputs:
    This function has no outputs. '''

    # Open a file corresponding to the path specified in savePath and write the data to its content. If the file does not 
    # already exist, it will be created. For safety, the data is cast to a string type again
    Path(folder).mkdir(parents=True, exist_ok=True)
    with open(Path(folder).resolve().joinpath(f"{filename}.{extension}"), 'w', encoding='utf-8') as out_file:
        #out_file.write(str(data)) # https://stackoverflow.com/questions/20101021/how-to-close-the-file-after-pickle-load-in-python
        json.dump(json.loads(data.replace("'", '"')), out_file, ensure_ascii=False, indent=4, default=default_converter)

def loadVariable(loadPath:str, variable:str) -> Any:
    ''' This function imports a variable from a .py file.
    
    Inputs:
    loadPath: a string specifying the path to the file to be loaded. This path must contain the filename and the
              extension .py.
    variable: a string specifying the name of the variable as it is given in the .py file to load

    
    Outputs:
    loadedVariable: a variable loaded from the file '''

    # get the folder and the filename
    folder = str(Path(loadPath).resolve().parent)
    filename = str(Path(loadPath).stem)

    # Add the relevant folder to the PYTHON PATH
    sys.path.append(folder)

    # import the file as a module
    loadModule = import_module(name=filename, package=folder)

    # get the variable from the loaded file loadModule and return it
    loadedVariable = getattr(loadModule, variable)  # https://stackoverflow.com/questions/68754829/from-module-import-variable-with-importlib
    return loadedVariable