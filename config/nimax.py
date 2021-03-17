config = dict()

# action library provides generator functions which produce action
# lists from input decision_id grouping
config["action_libraries"] = ["lisa_ANEC2"]

# we define all the servers here so that the overview is a bit better
config["servers"] = dict(
    nimax=dict(
        host="127.0.0.1",
        port=8006,
        group="server",
        fast="nidaqmx_server",
        params = dict(
            dev_CellCurrent = {
                        '1':'PXI-6289/ai16',
                        '2':'PXI-6289/ai17',
                        '3':'PXI-6289/ai18',
                        '4':'PXI-6289/ai19',
                        '5':'PXI-6289/ai20',
                        '6':'PXI-6289/ai21',
                        '7':'PXI-6289/ai22',
                        '8':'PXI-6289/ai23',
                        '9':'PXI-6289/ai0'
                        },
            dev_CelldiffV = {
                '1':'PXI-6284/ai16',
                '2':'PXI-6284/ai17',
                '3':'PXI-6284/ai18',
                '4':'PXI-6284/ai19',
                '5':'PXI-6284/ai20',
                '6':'PXI-6284/ai21',
                '7':'PXI-6284/ai22',
                '8':'PXI-6284/ai23',
                '9':'PXI-6284/ai0'
                },
            dev_ActiveCellsSelection = {
                '1':'PXI-6289/port0/line23',
                '2':'PXI-6289/port0/line24',
                '3':'PXI-6289/port0/line25',
                '4':'PXI-6289/port0/line26',
                '5':'PXI-6289/port0/line27',	
                '6':'PXI-6289/port0/line28',
                '7':'PXI-6289/port0/line29',
                '8':'PXI-6289/port0/line30',
                '9':'PXI-6289/port0/line31'
                },
            dev_FSWBCDCmd = {
                '1':'PXI-6284/port0/line0',
                '2':'PXI-6284/port0/line1',
                '3':'PXI-6284/port0/line2',
                '4':'PXI-6284/port0/line3'
                },
            dev_GasFlowValves = {
                '1':'PXI-6284/port1/line2',
                '2':'PXI-6284/port1/line3',	
                '3':'PXI-6284/port1/line4',
                '4':'PXI-6284/port1/line5',
                '5':'PXI-6284/port1/line6',
                '6':'PXI-6284/port1/line7',
                '7':'PXI-6284/port2/line7',
                '8':'PXI-6284/port2/line1',
                '9':'PXI-6284/port2/line2'
                },
            dev_MasterCellSelect = {
                '1':'PXI-6284/port0/line23',
                '2':'PXI-6284/port0/line24',
                '3':'PXI-6284/port0/line25',
                '4':'PXI-6284/port0/line26',
                '5':'PXI-6284/port0/line27',
                '6':'PXI-6284/port0/line28',
                '7':'PXI-6284/port0/line29',
                '8':'PXI-6284/port0/line30',
                '9':'PXI-6284/port0/line31',
                'X':'PXI-6284/port0/line22'              
                },
            dev_Pumps = {
                'PeriPump':'PXI-6284/port1/line0	',
                'MultiPeriPump':'PXI-6284/port1/line1'
                },
            dev_FSW = {
                'Done':'PXI-6284/port2/line4',
                'Error':'PXI-6284/port2/line6'                
                },
            dev_RSHTTLhandshake = {
                'port':'PXI-6284/ctr0',
                'term':'/PXI-6284/PFI8'
                }
        )
    ),
    exp_vis=dict(#simple dumb modular visualizer
        host="127.0.0.1",
        port=5008,
        group="visualizer",
        bokeh="bokeh_modular_visualizer",
        params = dict(
            doc_name = "ANEC2 visualizer",
            ws_nidaqmx="nimax",
        )
    ),
    orchestrator=dict(
        host="127.0.0.1",
        port=8010,
        group="orchestrators",
        fast="async_orch",
        path="."
    ),
)
