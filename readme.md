# getting started

## environment setup
- install miniconda[https://docs.conda.io/en/latest/miniconda.html], python 3.7 preferred
- clone git repository
- from repo directory, setup conda environment using `conda env create -f helao.yml`

## simulation servers
- galil and gamry server code current import from driver.*_simulate
- cd into server directory, execute start fastapi instances via  `python galil_server.py` and `python gamry_server.py`