import aiohttp
from helao.core.server import Base

class aligner:
    def __init__(self, actServ: Base):
        
        self.base = actServ
        self.config_dict = actServ.server_cfg["params"]
        self.C = actServ.world_cfg["servers"]
        # determines if an alignment is currently running
        # needed for visualizer
        # to signal end of alignment
        self.aligning = False
        # default instrument specific Transfermatrix
        self.Transfermatrix = [[1,0,0],[0,1,0],[0,0,1]]
        # for saving Transfermatrix
        self.newTransfermatrix = [[1,0,0],[0,1,0],[0,0,1]]
        # for saving errorcode
        self.errorcode = 0

        # TODO: Need to be replaced later for ORCH call, instead direct call
        self.motorserv = self.config_dict['motor_server']
        self.motorhost = self.C[self.motorserv]['host']
        self.motorport = self.C[self.motorserv]['port']

        self.visserv = self.config_dict['vis_server']
        self.vishost = self.C[self.visserv]['host']
        self.visport = self.C[self.visserv]['port']

        # TODO: need another way to get which data_server to use?
        # do this via orch call later
        self.dataserv = self.config_dict['data_server']
        self.datahost = self.C[self.dataserv]['host']
        self.dataport = self.C[self.dataserv]['port']


        # stores the plateid
        self.plateid = '4534' # have one here for testing, else put it to ''
        
        
    async def get_alignment(self, plateid, motor, data):
        self.aligning = True

        # Don't want to copy the complete config, which is also unnecessary
        # these are the params the Visulalizer needs
        self.plateid = plateid
        if motor in self.C.keys():
            self.motorhost = self.C[motor]['host']
            self.motorport = self.C[motor]['port']
            self.motorserv = motor
        else:
            print(f'Alignment Error. {motor} server not found.')
            return []

        if data in self.C.keys():
            self.datahost = self.C[data]['host']
            self.dataport = self.C[data]['port']
            self.dataserv = data
        else:
            print(f'Alignment Error. {data} server not found.')
            return []

#        if visualizer in self.C:
#            self.vishost = self.C[visualizer].host 
#            self.visport = self.C[visualizer].port
#            self.visserv= visualizer
#        else:
#            print(f'Alignment Error. {visualizer} server not found.')
#            return []

        print(f'Plate Aligner web interface: http://{self.vishost}:{self.visport}/{self.visserv}')
        
        
# alignement needs to be returned via status, else we get a timeout       
#        # now wait until bokeh server will set aligning to False via API call
#        while self.aligning:
#            await asyncio.sleep(1)            
#        # should not be needed?
#        self.aligning = False
            
        return {
            "err_code": self.errorcode,
            "plateid": self.plateid,
            "motor_server": self.motorserv,
            "data_server": self.dataserv
        }
    

    async def is_aligning(self):
        return self.aligning


    async def get_PM(self):

        url = f"http://{self.datahost}:{self.dataport}/{self.dataserv}/get_platemap_plateid"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={'plateid':self.plateid}) as resp:
                response = await resp.json()
                return response


    async def get_position(self):
        url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/query_positions"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={}) as resp:
                response = await resp.json()
                return response


    async def move(self, multi_d_mm, multi_axis, speed: int, mode):
        url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/move"
        pars = {
            'mulit_d_mm': multi_d_mm,
            'multi_axis': multi_axis,
            'speed': speed,
            'mode': mode
            }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=pars) as resp:
                response = await resp.json()
                return response


    async def plate_to_motorxy(self, platexy):
        url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/toMotorXY"
        pars = {'platexy':f"{platexy}"}       
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=pars) as resp:
                response = await resp.json()
                return response


    async def motor_to_platexy(self, motorxy):
        url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/toPlateXY"
        pars = {'motorxy':f"{motorxy}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=pars) as resp:
                response = await resp.json()
                return response
    

    async def ismoving(self, axis):
        url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/query_moving"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params={'axis':axis}) as resp:
                response = await resp.json()
                return response

    async def MxytoMPlate(self, Mxy):
        url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/MxytoMPlate"
        pars = {'Mxy':f"{Mxy}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=pars) as resp:
                response = await resp.json()
                return response

    # async def upload_alignmentmatrix(self):
    #     url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/upload_alignmentmatrix"
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(url, params={}) as resp:
    #             response = await resp.json()
    #             return response

    # async def download_alignmentmatrix(self, newxyTransfermatrix):
    #     url = f"http://{self.motorhost}:{self.motorport}/{self.motorserv}/download_alignmentmatrix"
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(url, params={'newxyTransfermatrix':json.dumps(newxyTransfermatrix.tolist())}) as resp:
    #             response = await resp.json()
    #             return np.asmatrix(json.loads(response))


################## END Helper functions #######################################