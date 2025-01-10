# HELAO public repository :robot: :rocket: :handshake: :woman_scientist: :man_scientist:
Helao deploys Hierachical Experimental Laboratory Automation and Orchestration
The idea behind this project is that we wanted to deploy active learning to different devices located in our laboratory and to others and even to many instruments running in parallel. To to this we utilized [fastAPI](https://fastapi.tiangolo.com/), a web framework that allows the facile developement of APIs. This project originated at Caltech and KIT and was later further advanced at TUM.

You may find the publicaton [here](https://doi.org/10.1002/admi.202101987)

The hdf5 files created during a simulated active learning run both in parallel and sequential instrument operation can be found [here](https://doi.org/10.6084/m9.figshare.16798177.v1)

![logo](https://github.com/helgestein/helao-dev/blob/master/helaologo.svg)

## Overview of branches and current versions

Since there are multiple versions of the HELAO, here is the brief overview all branches and versions:

| **Branch and repository**                                                      | **Description**                                                               | 
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| [helao-pub/master](https://github.com/helgestein/helao-pub/tree/master)        | The most actual version of the HELAO used at KIT and further developed at TUM |
| [helao-pub/backup](https://github.com/helgestein/helao-pub/tree/backup)        | The version as of the publication date with a minor corrections               |
| [helao-pub/SiGeSn](https://github.com/helgestein/helao-pub/tree/SiGeSn)        | The version used for exploration of Si-Ge-Sn anodes                           |
| [helao-async](https://github.com/High-Throughput-Experimentation/helao-async)  | The async version further developed and used at Caltech                       |
| [MISCHBARES](https://github.com/fuzhanrahmanian/MISCHBARES)                    | The further development of HELAO with built-in web interface and SQL database |

If you seek to make changes please do so but this will need permission from some of the contributors.

## Abstract

Materials acceleration platforms (MAPs) operate on the paradigm of integrating combinatorial synthesis, high-throughput characterization, automatic analysis and machine learning. Within these MAPs one or multiple autonomous feedback loops aim to optimize materials for certain functional properties or generate new insights. Fundamentally, this necessitates accelerated, but foremost integrated, research actions. Herein, a web based asynchronous protocol to seamlessly integrate research tasks within a hierarchical experimental laboratory automation and orchestration (HELAO) framework is presented. We demonstrate the capability of orchestrating distributed research instruments that may incorporate data from experiments, simulations, and databases. HELAO offers interfacing laboratory hardware and software distributed across several computers and operating systems for executing an experiment, data analysis, provenance tracking, and autonomous planning. Research acceleration in terms of reduction of total experimental time is demonstrated to be close to 2x (in addition to the speedup of active learning of 5-10x depending on active learning metric) by deploying a centrally orchestrated fleet of instruments for a active learning. To the best of our knowledge, HELAO is the only laboratory automation framework with integrated data management capable of running closed loop optimization on multiple instruments and extreme modularity.

## TL;DR

If you want to build autonomous labs that are spread around the globe use this framework - it might save you a lot of stress.

## Getting started

We have implemented a series of drivers and analysis techniques which you can easily reuse if you have the same or similar hardware.
Currently implemented devices in the laboratories at KIT and Caltech are shown in the table below. Instruments build from this include scanning droplet cells, high-throughput spectrometers and a battery assembly robot (all to be published elsewhere). The extreme modularity allows to mix and match any of these devices by simply defining a sequence of events i.e. to build an integrated SDC and spectrometer or a sample echange robot no code changes are necessary.
The currently implemented hardware is the following:
| **Device Name** | **Type**                      | **Communication**             | **Measures**     | **Manufacturer**          | **natively blocking** |
| --------------- | ----------------------------- | ----------------------------- | ---------------- | ------------------------- | --------------------- |
| lang            | Motion                        | .net API                      | position         | Lang GmbH                 | no                    |
| dobot           | Motion                        | TCP/IP                        | position         | Dobot Europe GmbH         | yes                   |
| galil           | Motion, IO                    | TCP/IP                        | position         | Galil Motion Control Inc. | no                    |
| owis            | Motion                        | serial commands               | position         | Owis GmbH                 | no                    |
| mecademic       | Motion                        | python TCP/IP API             | position, state  | Mecademic Ltd.            | no                    |
| rail            | Motion                        | TCP/IP                        | position         | Jenny Science AG          | no                    |
| autolab         | Potentiostat                  | .net API                      | electrochemistry | Methrohm Autolab B.V.     | yes                   |
| gamry           | Potentiostat                  | .dll for serial communication | electrochemistry | Gamry Instruments Inc.    | yes                   |
| arbin           | Potentiostat                  | autohotkey                    | electrochemistry | Arbin Inc.                | no                    |
| palmsens        | Potentiostat                  | .net API                      | electrochemistry | Palmsens B.V.             | yes                   |
| pump            | pumping                       | serial commands               | liquid volume    | CAT  engineering GmbH     | no                    |
| microlab        | pumping                       | TCP/IP                        | liquid volume    | Hamilton Company          | yes                   |
| psd             | pumping                       | serial commands               | liquid volume    | Hamilton Company          | no                    |
| arcoptix        | spectroscopy                  | .dll api                      | IR spectra       | arcoptix S.A.             | yes                   |
| ocean           | spectroscopy Raman            | python package                | Raman spectra    | ocean insights GmbH       | yes                   |
| force           | force sensing                 | serial commands               | force            | ME Meßsysteme GmbH        | n/a                   |
| arduino         | relays, I/O                   | python package                | n.a.             | arduino                   | no                    |
| kadi            | data management               | python package                | n.a.             | KIT                       | yes                   |
| aux             | machine learning and analysis | python package                | n.a.             | n.a.                      | yes                   |

There are dummy drivers and dummy analysis "devices" indicating how you can your own.

## Environment setup

HELAO is very lightweight and besides hardware drivers you just need a working python installation with fastAPI and starlette.
If you wish to setup thing super easy from scratch just follow these steps:
- install miniconda[https://docs.conda.io/en/latest/miniconda.html], python 3 only
- clone git repository
- from repo directory, setup conda environment using `conda env create -f helao.yml`

## Simulation servers
- galil and gamry server code current import from driver.*_simulate
- cd into server directory, execute start fastapi instances via  `python galil_server.py` and `python gamry_server.py`

## Launch script
- `helao.py` script can validate server configuration parameters, launch a group of servers, and shutdown all servers beloning to a group
- server groups may be defined as .py files in the `config/` folder (see `config/world.py` as an example)
- launch syntax: `python helao.py world` will validate and launch servers with parameters defined in `config/world.py`, while also writing all monitored process IDs to `pids_world.pck` in the root directory
- exercise caution when running multiple server groups as there is currently no check for ports that are currently in-use between different config files

Alternatively:
- `python testing\helao_interface.py world` syntax from root directory will launch a GUI with servers defined in `config/world.py`
- open all servers and driver servers required for the experimentation

## Design
High level layout of HELAO where experiments are executed by sequentially calling actions which are high level wrappers for other actions or low level driver instructions. Communication goes hierarchically down from the orchestrator level to actions, which may communicate with one another, to the lowest level of drivers which may only communicate with the calling action. The orchestrator, actions and drivers are all exposing python class functions through a web interface allowing for a modular and distributed hosting of each item. Experiments are dictionaries containing a sequence of events (SOE) that outlines in which the actions are to be executed. All actions require parameters and are supplied with experiment level metadata. Metadata may be introduced at any level.
![helao](figure_1.png)

## List of updates

- Stable with Python 3.12
- New instruments are added: PalmSens4 potentiostat, Dobot M1 Pro robotic arm, PSD/4 Hamilton Pump
- New visualizer for PalmSens (based on Matplotlib)
- Fixed minor bugs in Orchestrator, ML and analysis servers, etc.

## Acknowledgements

This project has received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement [No 957189](https://cordis.europa.eu/project/id/957189).
