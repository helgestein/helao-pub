import sys
from importlib import import_module

import uvicorn

confPrefix = sys.argv[1]
servKey = sys.argv[2]
config = import_module(f"helao.config.{confPrefix}").config
C = config["servers"]
S = C[servKey]

makeApp = import_module(f"helao.library.server.{S['group']}.{S['fast']}").makeApp
app = makeApp(confPrefix, servKey)

if __name__ == "__main__":
    uvicorn.run(app, host=S['host'], port=S['port'])
