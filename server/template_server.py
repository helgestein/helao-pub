"""
basic mandatory imports below
"""
import sys
import uvicorn
from fastapi import FastAPI
import os
from importlib import import_module

"""
importation of the config file
"""
helao_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(helao_root, 'config'))
sys.path.append(os.path.join(helao_root, 'driver'))
sys.path.append(helao_root)
#from template_driver import template
config = import_module(sys.argv[1]).config
serverkey = sys.argv[2]


"""
defines fastapi app
"""
app = FastAPI(title="template server", 
    description="This is a fancy template action server", 
    version="1.0")


"""
instantiate device object on server startup
"""
@app.on_event("startup")
def startup_event():
    global t
    #t = template(config[serverkey])



""""
below are two example action functions. these have several features
1st, they must have the fastapi function decorator
below the def statement is the body of the function, which communicates with one or more driver servers via requests.get
lastly, we have the return dictionary, which should record all inputs and outputs to the function and lower-level functions 
"""
@app.get("/templateDriver/function_one")
def function_one(var1, var2):
    global t
    data = t.function_one(var1,var2)
    retc = dict(parameters={'var1':var1,'var2':var2}, data=data)
    return retc

@app.get("/templateDriver/function_two")
def function_two(var1):
    global t
    data = t.function_two(var1)
    retc = dict(parameters={"var1":var1},data=data)
    return retc


if __name__ == "__main__":
    """
    run app
    """
    uvicorn.run(app,host=config['servers'][serverkey]['host'],port=config['servers'][serverkey]['port'])

