""" A device class for the Galil motion controller, used by a FastAPI server instance.

The 'galil' device class exposes motion and I/O functions from the underlying 'gclib'
library. Class methods are specific to Galil devices. Device configuration is read from
config/config.py. 
"""

import os
import numpy as np
import time
import pathlib
import asyncio
from enum import Enum

from helao.core.server import Base

driver_path = os.path.dirname(__file__)

# install galil driver first
# (helao) c:\Program Files (x86)\Galil\gclib\source\wrappers\python>python setup.py install
import gclib

# pathlib.Path(os.path.join(helao_root, 'visualizer\styles.css')).read_text()


class cmd_exception(ValueError):
    def __init__(self, arg):
        self.args = arg


class galil:
    def __init__(self, actServ: Base):

        self.base = actServ
        self.config_dict = actServ.server_cfg["params"]

        self.config_dict["estop_motor"] = False
        self.config_dict["estop_io"] = False
        if not "tbroadcast" in self.config_dict:
            self.config_dict["tbroadcast"] = 2  # sec
        self.tbroadcast = self.config_dict["tbroadcast"]

        # need to check if config settings exist
        # else need to create empty ones
        if "axis_id" not in self.config_dict:
            self.config_dict["axis_id"] = dict()

        if "Din_id" not in self.config_dict:
            self.config_dict["Din_id"] = dict()

        if "Dout_id" not in self.config_dict:
            self.config_dict["Dout_id"] = dict()

        if "Aout_id" not in self.config_dict:
            self.config_dict["Aout_id"] = dict()

        if "Ain_id" not in self.config_dict:
            self.config_dict["Ain_id"] = dict()

        print(" ... motor config:", self.config_dict)

        # this is only here for testing purposes to supply a matrix
        if "Transfermatrix" not in self.config_dict:
            self.config_dict["Transfermatrix"] = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

        if "M_instr" not in self.config_dict:
            self.config_dict["M_instr"] = [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ]

        self.xyTransfermatrix = np.matrix(self.config_dict["Transfermatrix"])

        # Mplatexy is identity matrix by default
        self.transform = transformxy(
            self.config_dict["M_instr"], self.config_dict["axis_id"]
        )
        # only here for testing: will overwrite the default identity matrix
        self.transform.update_Mplatexy(self.config_dict["Transfermatrix"])
        #        self.transform.update_Msystem()
        print(" ... M_instr:", self.transform.Minstr)
        print(" ... M_plate:", self.transform.Mplate)

        # if this is the main instance let us make a galil connection
        self.g = gclib.py()
        print("gclib version:", self.g.GVersion())
        # TODO: error checking here: Galil can crash an dcarsh program
        try:
            self.g.GOpen("%s --direct -s ALL" % (self.config_dict["galil_ip_str"]))
            print(self.g.GInfo())
            self.c = self.g.GCommand  # alias the command callable
        except Exception:
            # todo retrzy counter
            print("###########################################################")
            print(
                " ........................... severe Galil error ... please power cycle Galil and try again"
            )
            print("###########################################################")

        self.cycle_lights = False

        self.qdata = asyncio.Queue(maxsize=500)  # ,loop=asyncio.get_event_loop())

        # local buffer for motion data streaming
        # nees to be upated by every motion function
        self.wsmotordata_buffer = dict(
            axis=[axis for axis in self.config_dict["axis_id"].keys()],
            axisid=[axisid for _, axisid in self.config_dict["axis_id"].items()],
            motor_status=["stopped" for axis in self.config_dict["axis_id"].keys()],
            err_code=[0 for axis in self.config_dict["axis_id"].keys()],
            position=[0.0 for axis in self.config_dict["axis_id"].keys()],
            platexy=[0.0, 0.0, 1],
        )

    def update_wsmotorbufferall(self, datakey, dataitems):
        if datakey in self.wsmotordata_buffer.keys():
            self.wsmotordata_buffer[datakey] = dataitems

        # update plateposition
        if datakey == "position":
            self.motor_to_plate_calc()

        if self.qdata.full():
            # print(' ... motion q is full ...')
            _ = self.qdata.get_nowait()
        self.qdata.put_nowait(self.wsmotordata_buffer)

    def update_wsmotorbuffersingle(self, datakey, ax, item):
        if datakey in self.wsmotordata_buffer.keys():
            if ax in self.wsmotordata_buffer["axis"]:
                idx = self.wsmotordata_buffer["axis"].index(ax)
                self.wsmotordata_buffer[datakey][idx] = item

        # update plateposition
        if datakey == "position":
            self.motor_to_plate_calc()

        if self.qdata.full():
            # print(' ... motion q is full ...')
            _ = self.qdata.get_nowait()
        self.qdata.put_nowait(self.wsmotordata_buffer)

    async def setaxisref(self):
        # home all axis first
        axis = await self.get_all_axis()
        print(" ... axis:", axis)
        if "Rx" in axis:
            axis.remove("Rx")
        if "Ry" in axis:
            axis.remove("Ry")
        if "Rz" in axis:
            axis.remove("Rz")
        #            axis.pop(axis.index('Rz'))
        print(" ... axis:", axis)

        if axis is not None:
            # go slow to find the same position every time
            # first a fast move to find the switch
            retc1 = await self.motor_move(
                [0 for ax in axis], axis, None, move_modes.homing
            )
            # move back 2mm
            retc1 = await self.motor_move(
                [2 for ax in axis], axis, None, move_modes.relative
            )
            # approach switch again very slow to get better zero position
            retc1 = await self.motor_move(
                [0 for ax in axis], axis, 1000, move_modes.homing
            )

            retc2 = await self.motor_move(
                [
                    self.config_dict["axis_zero"][self.config_dict["axis_id"][ax]]
                    for ax in axis
                ],
                [ax for ax in axis],
                None,
                move_modes.relative,
            )

            # set absolute zero to current position
            q = self.c("TP")  # query position of all axis
            print(" ... q1", q)
            cmd = "DP "
            for i in range(len(q.split(","))):
                if i == 0:
                    cmd += "0"
                else:
                    cmd += ",0"
            print(" ... ", cmd)

            # sets abs zero here
            _ = self.c(cmd)

            return retc2
        else:
            return "error"

    def motor_to_plate_calc(self):
        # add some extra data
        if "x" in self.wsmotordata_buffer["axis"]:
            idx = self.wsmotordata_buffer["axis"].index("x")
            xmotor = self.wsmotordata_buffer["position"][idx]
        else:
            xmotor = None

        if "y" in self.wsmotordata_buffer["axis"]:
            idx = self.wsmotordata_buffer["axis"].index("y")
            ymotor = self.wsmotordata_buffer["position"][idx]
        else:
            ymotor = None
        platexy = self.transform.transform_motorxy_to_platexy([xmotor, ymotor, 1])
        self.wsmotordata_buffer["platexy"] = [platexy[0], platexy[1], 1]

    async def motor_move(self, multi_d_mm, multi_axis, speed, mode):
        stopping = False  # no stopping of any movement by other actions
        # this function moves the motor by a set amount of milimeters
        # you have to specify the axis,
        # if no axis is specified this function throws an error
        # if no speed is specified we use the default slow speed
        # as specified in the setupdict

        # example: move the motor 5mm to the positive direction:
        # motor_move(5,'x')
        # example: move the motor to absolute 0 mm
        # motor_move(5,'x',mode='absolute')
        # home the motor at low speed (the distance is not used)
        # motor_move(5,'x',mode='homing',speed=10000)
        # multi axis move:
        # motor_move([5, 10],['x', 'y'],mode='absolute',speed=10000)
        # the server call would look like:
        # http://127.0.0.1:8001/motor/set/move?d_mm=-20&axis=x&mode=relative
        # http://127.0.0.1:8001/motor/set/move?d_mm=-20&axis=x&mode=absolute

        # convert single axis move to list
        if type(multi_d_mm) is not list:
            multi_axis = [multi_axis]
            multi_d_mm = [multi_d_mm]

        # return value arrays for multi axis movement
        ret_moved_axis = []
        ret_speed = []
        ret_accepted_rel_dist = []
        ret_supplied_rel_dist = []
        ret_err_dist = []
        ret_err_code = []
        ret_counts = []

        # expected time for each move, used for axis stop check
        timeofmove = []

        if self.config_dict["estop_motor"] == True:
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": None,
                "err_dist": None,
                "err_code": "estop",
                "counts": None,
            }

        # TODO: if same axis is moved twice
        for d_mm, axis in zip(multi_d_mm, multi_axis):
            # need to remove stopping for multi-axis move
            if len(ret_moved_axis) > 0:
                stopping = False

            # first we check if we have the right axis specified
            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
            else:
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(d_mm)
                ret_err_dist.append(None)
                ret_err_code.append("setup")
                ret_counts.append(None)
                continue

            # check if the motors are moving if so return an error message
            # recalculate the distance in mm into distance in counts
            try:
                print(" ... count_to_mm:", ax, self.config_dict["count_to_mm"][ax])
                float_counts = (
                    d_mm / self.config_dict["count_to_mm"][ax]
                )  # calculate float dist from steupd

                counts = int(np.floor(float_counts))  # we can only mode full counts
                # save and report the error distance
                error_distance = self.config_dict["count_to_mm"][ax] * (
                    float_counts - counts
                )

                # check if a speed was upplied otherwise set it to standart
                if speed == None:
                    speed = self.config_dict["def_speed_count_sec"]
                else:
                    speed = int(np.floor(speed))

                if speed > self.config_dict["max_speed_count_sec"]:
                    speed = self.config_dict["max_speed_count_sec"]
                self._speed = speed
            except Exception:
                # something went wrong in the numerical part so we give that as feedback
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(d_mm)
                ret_err_dist.append(None)
                ret_err_code.append("numerical")
                ret_counts.append(None)
                continue

            try:
                # the logic here is that we assemble a command sequence
                # here we decide if we move relative, home, or move absolute
                if stopping:
                    # cmd_seq = ["AB", "MO{}".format(ax), "SH{}".format(ax), "SP{}={}".format(ax, speed)]
                    cmd_seq = [
                        "ST{}".format(ax),
                        "MO{}".format(ax),
                        "SH{}".format(ax),
                        "SP{}={}".format(ax, speed),
                    ]
                else:
                    cmd_seq = ["SP{}={}".format(ax, speed)]
                if mode == move_modes.relative:
                    cmd_seq.append("PR{}={}".format(ax, counts))
                elif mode == move_modes.homing:
                    cmd_seq.append("HM{}".format(ax))
                elif mode == move_modes.absolute:
                    # now we want an abolute position
                    cmd_seq.append("PA{}={}".format(ax, counts))
                else:
                    raise cmd_exception
                cmd_seq.append("BG{}".format(ax))
                # todo: fix this for absolute or relative move
                timeofmove.append(abs(counts / speed))

                # ret = ""
                print("BUGCHECK:", cmd_seq)
                # BUG
                # TODO
                # it can happen that it crashes below for some reasons
                # when more then two axis move are requested
                for cmd in cmd_seq:
                    _ = self.c(cmd)
                    # ret.join(_)
                print(" ... Galil cmd:", cmd_seq)
                ret_moved_axis.append(ax)
                ret_speed.append(speed)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(d_mm)
                ret_err_dist.append(error_distance)
                ret_err_code.append(0)
                ret_counts.append(counts)
                # time = counts/ counts_per_second

                continue
            except Exception:
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(d_mm)
                ret_err_dist.append(None)
                ret_err_code.append("motor")
                ret_counts.append(None)
                continue

        # get max time until all axis are expected to have stopped
        print(" ... timeofmove", timeofmove)
        if len(timeofmove) > 0:
            tmax = max(timeofmove)
            if tmax > 30 * 60:
                tmax > 30 * 60  # 30min hard limit
        else:
            tmax = 0

        # wait for expected axis move time before checking if axis stoppped
        print(" ... axis expected to stop in", tmax, "sec")

        if self.config_dict["estop_motor"] == False:

            # check if all axis stopped
            tstart = time.time()
            if "timeout" in self.config_dict:
                tout = self.config_dict["timeout"]
            else:
                tout = 60
            while (time.time() - tstart < tout) and self.config_dict[
                "estop_motor"
            ] == False:
                qmove = await self.query_axis_moving(multi_axis)
                #                time.sleep(0.5) # TODO: what time is ok to wait and not to overload the Galil
                await asyncio.sleep(0.5)
                if all(qmove["err_code"]):
                    break

            if self.config_dict["estop_motor"] == False:
                # stop of motor movement (motor still on)
                if time.time() - tstart > tout:
                    await self.stop_axis(multi_axis)
                # check which axis had the timeout
                newret_err_code = []
                for erridx, err_code in enumerate(ret_err_code):
                    if qmove["err_code"][erridx] == 0:
                        newret_err_code.append("timeout")
                    else:
                        newret_err_code.append(err_code)

                ret_err_code = newret_err_code
            else:
                # estop occured while checking axis end position
                ret_err_code = ["estop" for _ in ret_err_code]

        else:
            # estop was triggered while waiting for axis to stop
            ret_err_code = ["estop" for _ in ret_err_code]

        # read final position
        # updates ws buffer
        _ = await self.query_axis_position(multi_axis)

        # one return for all axis
        return {
            "moved_axis": ret_moved_axis,
            "speed": ret_speed,
            "accepted_rel_dist": ret_accepted_rel_dist,
            "supplied_rel_dist": ret_supplied_rel_dist,
            "err_dist": ret_err_dist,
            "err_code": ret_err_code,
            "counts": ret_counts,
        }

    async def motor_disconnect(self):
        try:
            self.g.GClose()  # don't forget to close connections!
        except gclib.GclibError as e:
            return {"connection": {"Unexpected GclibError:", e}}
        return {"connection": "motor_offline"}

    async def query_axis_position(self, multi_axis):
        # this only queries the position of a single axis
        # server example:
        # http://127.0.0.1:8000/motor/query/position?axis=x

        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]

        # first get the relative position (actual only the current position of the encoders)
        # to get how many axis are present
        q = self.c("TP")  # query position of all axis
        cmd = "PA "
        for i in range(len(q.split(","))):
            if i == 0:
                cmd += "?"
            else:
                cmd += ",?"
        q = self.c(cmd)  # query position of all axis
        # _ = self.c("PF 10.4")  # set format
        # q = self.c("TP")  # query position of all axis

        # now we need to map these outputs to the ABCDEFG... channels
        # and then map that to xyz so it is humanly readable
        axlett = "ABCDEFGH"
        axlett = axlett[0 : len(q.split(","))]
        inv_axis_id = {d: v for v, d in self.config_dict["axis_id"].items()}
        ax_abc_to_xyz = {l: inv_axis_id[l] for i, l in enumerate(axlett)}
        # this puts the counts back to motor mm
        pos = {
            axl: int(r) * self.config_dict["count_to_mm"][axl]
            for axl, r in zip(axlett, q.split(", "))
        }
        # return the results through calculating things into mm
        axpos = {ax_abc_to_xyz[k]: p for k, p in pos.items()}
        ret_ax = []
        ret_position = []
        for axis in multi_axis:
            if axis in axpos.keys():
                self.update_wsmotorbuffersingle("position", axis, axpos[axis])
                ret_ax.append(axis)
                ret_position.append(axpos[axis])
            else:
                ret_ax.append(None)
                ret_position.append(None)

        return {"ax": ret_ax, "position": ret_position}

    async def query_axis_moving(self, multi_axis):
        # this functions queries the status of the axis
        q = self.c("SC")
        axlett = "ABCDEFGH"
        axlett = axlett[0 : len(q.split(","))]
        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]
        ret_status = []
        ret_err_code = []
        qdict = dict(zip(axlett, q.split(", ")))
        for axis in multi_axis:
            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
                if ax in qdict:
                    r = qdict[ax]
                    if int(r) == 0:
                        self.update_wsmotorbuffersingle("motor_status", axis, "moving")
                        self.update_wsmotorbuffersingle("err_code", axis, int(r))
                        ret_status.append("moving")
                        ret_err_code.append(int(r))
                    elif int(r) == 1:
                        self.update_wsmotorbuffersingle("motor_status", axis, "stopped")
                        self.update_wsmotorbuffersingle("err_code", axis, int(r))
                        ret_status.append("stopped")
                        ret_err_code.append(int(r))
                    else:
                        self.update_wsmotorbuffersingle("motor_status", axis, "stopped")
                        self.update_wsmotorbuffersingle("err_code", axis, int(r))
                        # stopped due to error/issue
                        ret_status.append("stopped")
                        ret_err_code.append(int(r))
                else:
                    ret_status.append("invalid")
                    ret_err_code.append(-1)

            else:
                ret_status.append("invalid")
                ret_err_code.append(-1)
                pass

        return {"motor_status": ret_status, "err_code": ret_err_code}

    async def reset(self):
        # The RS command resets the state of the processor to its power-on condition.
        # The previously saved state of the controller,
        # along with parameter values, and saved sequences are restored.
        return self.c("RS")

    async def estop_axis(self, switch):
        # this will estop the axis
        # set estop: switch=true
        # release estop: switch=false
        print("Axis Estop")
        if switch == True:
            await self.stop_axis(await self.get_all_axis())
            await self.motor_off(await self.get_all_axis())
            # set flag (move command need to check for it)
            self.config_dict["estop_motor"] = True
        else:
            # need only to set the flag
            self.config_dict["estop_motor"] = False

    async def estop_io(self, switch):
        # this will estop the io
        # set estop: switch=true
        # release estop: switch=false
        print("IO Estop")
        if switch == True:
            await self.break_infinite_digital_cycles()
            await self.digital_out_off(await self.get_all_digital_out())
            await self.set_analog_out(await self.get_all_analoh_out(), 0)
            # set flag
            self.config_dict["estop_io"] = True
        else:
            # need only to set the flag
            self.config_dict["estop_io"] = False

    async def stop_axis(self, multi_axis):
        # this will stop the current motion of the axis
        # but not turn off the motor
        # for stopping and turnuing off use moto_off

        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]
        for axis in multi_axis:
            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
                self.c("ST{}".format(ax))

        ret = await self.query_axis_moving(multi_axis)
        ret.update(await self.query_axis_position(multi_axis))
        return ret

    async def motor_off(self, multi_axis):

        # sometimes it is useful to turn the motors off for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors

        # an example would be:
        # http://127.0.0.1:8000/motor/stop
        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]

        for axis in multi_axis:

            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
            else:
                continue
                # ret = self.query_axis_moving(multi_axis)
                # ret.update(self.query_axis_position(multi_axis))
                # return ret

            # cmd_seq = ["AB", "MO{}".format(ax)]
            cmd_seq = ["ST{}".format(ax), "MO{}".format(ax)]

            for cmd in cmd_seq:
                _ = self.c(cmd)

        ret = await self.query_axis_moving(multi_axis)
        ret.update(await self.query_axis_position(multi_axis))
        return ret

    async def motor_on(self, multi_axis):
        # sometimes it is useful to turn the motors back on for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors
        # server example
        # http://127.0.0.1:8000/motor/on?axis=x

        # convert single axis move to list
        if type(multi_axis) is not list:
            multi_axis = [multi_axis]

        for axis in multi_axis:

            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
            else:
                continue
                # ret = self.query_axis_moving(multi_axis)
                # ret.update(self.query_axis_position(multi_axis))
                # return ret
            # cmd_seq = ["AB", "SH{}".format(ax)]
            cmd_seq = ["ST{}".format(ax), "SH{}".format(ax)]

            for cmd in cmd_seq:
                _ = self.c(cmd)

        ret = await self.query_axis_moving(multi_axis)
        ret.update(await self.query_axis_position(multi_axis))
        return ret

    async def read_analog_in(self, multi_port):
        # this reads the value of an analog in port
        # http://127.0.0.1:8000/
        if type(multi_port) is not list:
            multi_port = [multi_port]
        ret = []
        for port in multi_port:
            if port in self.config_dict["Ain_id"].keys():
                pID = self.config_dict["Ain_id"][port]
                ret.append(self.c("@AN[{}]".format(int(pID))))
            else:
                ret.append("AI ERROR")
        return {"port": multi_port, "value": ret, "type": "analog_in"}

    async def read_digital_in(self, multi_port):
        # this reads the value of a digital in port
        # http://127.0.0.1:8000/
        if type(multi_port) is not list:
            multi_port = [multi_port]
        ret = []
        for port in multi_port:
            if port in self.config_dict["Din_id"].keys():
                pID = self.config_dict["Din_id"][port]
                ret.append(self.c("@IN[{}]".format(int(pID))))
            else:
                ret.append("DI ERROR")
        return {"port": multi_port, "value": ret, "type": "digital_in"}

    async def read_digital_out(self, multi_port):
        # this reads the value of an digital out port i.e. what is
        # actuallybeing put out (for checking)
        # http://127.0.0.1:8000/
        if type(multi_port) is not list:
            multi_port = [multi_port]
        ret = []
        for port in multi_port:
            if port in self.config_dict["Dout_id"].keys():
                pID = self.config_dict["Dout_id"][port]
                ret.append(self.c("@OUT[{}]".format(int(pID))))
            else:
                ret.append("DO ERROR")
        return {"port": multi_port, "value": ret, "type": "digital_out"}

    # def set_analog_out(self, multi_port, handle: int, module: int, bitnum: int, multi_value):
    async def set_analog_out(self, multi_port, multi_value):
        # this is essentially a placeholder for now since the DMC-4143 does not support
        # analog out but I believe it is worthwhile to have this in here for the RIO
        # Handle num is A-H and must be on port 502 for the modbus commons
        # module is the position of the module from 1 to 16
        # bitnum is the IO point in the module from 1-4
        # the fist value n_0
        # n_0 = handle * 1000 + (module - 1) * 4 + bitnum
        # _ = self.c("AO {},{}".format(port, value))
        return {"port": multi_port, "value": multi_value, "type": "analog_out"}

    async def digital_out_on(self, multi_port):
        if type(multi_port) is not list:
            multi_port = [multi_port]
        for port in multi_port:
            if port in self.config_dict["Dout_id"].keys():
                pID = self.config_dict["Dout_id"][port]
                _ = self.c("SB {}".format(int(pID)))
        return {
            "port": multi_port,
            "value": await self.read_digital_out(multi_port),
            "type": "digital_out",
        }

    async def digital_out_off(self, multi_port):
        if type(multi_port) is not list:
            multi_port = [multi_port]

        for port in multi_port:
            if port in self.config_dict["Dout_id"].keys():
                pID = self.config_dict["Dout_id"][port]
                _ = self.c("CB {}".format(int(pID)))
        return {
            "port": multi_port,
            "value": await self.read_digital_out(multi_port),
            "type": "digital_out",
        }

    async def upload_DMC(self, DMC_prog):
        self.c("UL;")  # begin upload
        # upload line by line from DMC_prog
        for DMC_prog_line in DMC_prog.split("\n"):
            self.c(DMC_prog_line)
        self.c("\x1a")  # terminator "<cntrl>Z"

    async def set_digital_cycle(self, trigger_port, out_port, t_cycle):
        DMC_prog = pathlib.Path(
            os.path.join(driver_path, "galil_toogle.dmc")
        ).read_text()
        DMC_prog = DMC_prog.format(
            p_trigger=trigger_port, p_output=out_port, t_time=t_cycle
        )
        self.upload_DMC(DMC_prog)
        # self.c("XQ")
        self.c("XQ #main")  # excecute main routine

    async def infinite_digital_cycles(
        self, on_time=0.2, off_time=0.2, port=0, init_time=0
    ):
        self.cycle_lights = True
        time.sleep(init_time)
        while self.cycle_lights:
            await self.digital_out_on(port)
            time.sleep(on_time)
            await self.digital_out_off(port)
            time.sleep(off_time)
        return {
            "port": port,
            "value": "ran_infinite_light_cycles",
            "type": "digital_out",
        }

    async def break_infinite_digital_cycles(
        self, on_time=0.2, off_time=0.2, port=0, init_time=0
    ):
        self.cycle_lights = False

    async def get_all_axis(self):
        return [axis for axis in self.config_dict["axis_id"].keys()]

    async def get_all_digital_out(self):
        return [port for port in self.config_dict["Dout_id"].keys()]

    async def get_all_digital_in(self):
        return [port for port in self.config_dict["Din_id"].keys()]

    async def get_all_analog_out(self):
        return [port for port in self.config_dict["Aout_id"].keys()]

    async def get_all_analog_in(self):
        return [port for port in self.config_dict["Ain_id"].keys()]

    def shutdown_event(self):
        # this gets called when the server is shut down or reloaded to ensure a clean
        # disconnect ... just restart or terminate the server
        # self.stop_axis(self.get_all_axis())
        print(" ... shutting down galil motion")
        # asyncio.gather(self.motor_off(asyncio.gather(self.get_all_axis()))) # already contains stop command
        self.g.GClose()
        return {"shutdown"}


class move_modes(str, Enum):
    homing = "homing"
    relative = "relative"
    absolute = "absolute"


class transformation_mode(str, Enum):
    motorxy = "motorxy"
    platexy = "platexy"
    instrxy = "instrxy"


class transformxy:
    # Updating plate calibration will automatically update the system transformation
    # matrix. When angles are changed updated them also here and run update_Msystem
    def __init__(self, Minstr, seq=None):
        # instrument specific matrix
        # motor to instrument
        self.Minstrxyz = np.asmatrix(Minstr)  # np.asmatrix(np.identity(4))
        self.Minstr = np.asmatrix(np.identity(4))
        self.Minstrinv = np.asmatrix(np.identity(4))
        # plate Matrix
        # instrument to plate
        self.Mplate = np.asmatrix(np.identity(4))
        self.Mplatexy = np.asmatrix(np.identity(3))
        # system Matrix
        # motor to plate
        self.M = np.asmatrix(np.identity(4))
        self.Minv = np.asmatrix(np.identity(4))
        # need to update the angles here each time the axis is rotated
        self.alpha = 0
        self.beta = 0
        self.gamma = 0
        self.seq = seq

        # pre calculates the system Matrix M
        self.update_Msystem()
        print(" ... Minstr", self.Minstr)
        print(" ... Minstrxyz", self.Minstrxyz)

    def transform_platexy_to_motorxy(self, platexy):
        """simply calculates motorxy based on platexy
        plate warping (z) will be a different call"""
        platexy = np.asarray(platexy)
        if len(platexy) == 3:
            platexy = np.insert(platexy, 2, 0)
        # for _ in range(4-len(platexy)):
        #     platexy = np.append(platexy,1)
        print(" ... M:\n", self.M)
        print(" ... xy:", platexy)
        motorxy = np.dot(self.M, platexy)
        motorxy = np.delete(motorxy, 2)
        motorxy = np.array(motorxy)[0]
        return motorxy

    def transform_motorxy_to_platexy(self, motorxy):
        """simply calculates platexy from current motorxy"""
        motorxy = np.asarray(motorxy)
        if len(motorxy) == 3:
            motorxy = np.insert(motorxy, 2, 0)
        print(" ... Minv:\n", self.Minv)
        print(" ... xy:", motorxy)
        platexy = np.dot(self.Minv, motorxy)
        platexy = np.delete(platexy, 2)
        platexy = np.array(platexy)[0]
        return platexy

    def transform_motorxyz_to_instrxyz(self, motorxyz):
        """simply calculatesinstrxyz from current motorxyz"""
        motorxyz = np.asarray(motorxyz)
        if len(motorxyz) == 3:
            # append 1 at end
            motorxyz = np.append(motorxyz, 1)
        print(" ... Minstrinv:\n", self.Minstrinv)
        print(" ... xyz:", motorxyz)
        instrxyz = np.dot(self.Minstrinv, motorxyz)
        return np.array(instrxyz)[0]

    def transform_instrxyz_to_motorxyz(self, instrxyz):
        """simply calculates motorxyz from current instrxyz"""
        instrxyz = np.asarray(instrxyz)
        if len(instrxyz) == 3:
            instrxyz = np.append(instrxyz, 1)
        print(" ... Minstr:\n", self.Minstr)
        print(" ... xyz:", instrxyz)

        motorxyz = np.dot(self.Minstr, instrxyz)
        return np.array(motorxyz)[0]

    def Rx(self):
        """returns rotation matrix around x-axis"""
        alphatmp = np.mod(self.alpha, 360)  # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if alphatmp == 0:  # or alphatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif alphatmp == 90:  # or alphatmp == -270:
            return np.matrix([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
        elif alphatmp == 180:  # or alphatmp == -180:
            return np.matrix([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        elif alphatmp == 270:  # or alphatmp == -90:
            return np.matrix([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]])
        else:
            return np.matrix(
                [
                    [1, 0, 0, 0],
                    [
                        0,
                        np.cos(np.pi / 180 * alphatmp),
                        -1.0 * np.sin(np.pi / 180 * alphatmp),
                        0,
                    ],
                    [
                        0,
                        np.sin(np.pi / 180 * alphatmp),
                        np.cos(np.pi / 180 * alphatmp),
                        0,
                    ],
                    [0, 0, 0, 1],
                ]
            )

    def Ry(self):
        """returns rotation matrix around y-axis"""
        betatmp = np.mod(self.beta, 360)  # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if betatmp == 0:  # or betatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif betatmp == 90:  # or betatmp == -270:
            return np.matrix([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]])
        elif betatmp == 180:  # or betatmp == -180:
            return np.matrix([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        elif betatmp == 270:  # or betatmp == -90:
            return np.matrix([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]])
        else:
            return np.matrix(
                [
                    [
                        np.cos(np.pi / 180 * self.beta),
                        0,
                        np.sin(np.pi / 180 * self.beta),
                        0,
                    ],
                    [0, 1, 0, 0],
                    [
                        -1.0 * np.sin(np.pi / 180 * self.beta),
                        0,
                        np.cos(np.pi / 180 * self.beta),
                        0,
                    ],
                    [0, 0, 0, 1],
                ]
            )

    def Rz(self):
        """returns rotation matrix around z-axis"""
        gammatmp = np.mod(self.gamma, 360)  # this actually takes care of neg. values
        # precalculate some common angles for better accuracy and speed
        if gammatmp == 0:  # or gammatmp == -0.0:
            return np.asmatrix(np.identity(4))
        elif gammatmp == 90:  # or gammatmp == -270:
            return np.matrix([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        elif gammatmp == 180:  # or gammatmp == -180:
            return np.matrix([[-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        elif gammatmp == 270:  # or gammatmp == -90:
            return np.matrix([[0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        else:
            return np.matrix(
                [
                    [
                        np.cos(np.pi / 180 * gammatmp),
                        -1.0 * np.sin(np.pi / 180 * gammatmp),
                        0,
                        0,
                    ],
                    [
                        np.sin(np.pi / 180 * gammatmp),
                        np.cos(np.pi / 180 * gammatmp),
                        0,
                        0,
                    ],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ]
            )

    def Mx(self):
        """returns Mx part of Minstr"""
        Mx = np.asmatrix(np.identity(4))
        Mx[0, 0:4] = self.Minstrxyz[0, 0:4]
        print(" ... Mx", Mx)
        return Mx

    def My(self):
        """returns My part of Minstr"""
        My = np.asmatrix(np.identity(4))
        My[1, 0:4] = self.Minstrxyz[1, 0:4]
        print(" ... My", My)
        return My

    def Mz(self):
        """returns Mz part of Minstr"""
        Mz = np.asmatrix(np.identity(4))
        Mz[2, 0:4] = self.Minstrxyz[2, 0:4]
        print(" ... Mz", Mz)
        return Mz

    def Mplatewarp(self, platexy):
        """returns plate warp correction matrix (Z-correction. 
        Only valid for a single platexy coordinate"""
        return np.asmatrix(np.identity(4))  # TODO, just returns identity matrix for now

    def update_Msystem(self):
        """updates the transformation matrix for new plate calibration or
        when angles are changed.
        Follows stacking sequence from bottom to top (plate)"""

        print(" ... updatting M")

        if self.seq == None:
            print(" ... seq is empty, using default transformation")
            # default case, we simply have xy calibration
            self.M = np.dot(self.Minstrxyz, self.Mplate)
        else:
            self.Minstr = np.asmatrix(np.identity(4))
            # more complicated
            # check for some common sequences:
            Mcommon1 = (
                False  # to check against when common combinations are already found
            )
            axstr = ""
            for ax in self.seq.keys():
                axstr += ax
            # check for xyz or xy (with no z)
            # sequence does not matter so should define it like this in the config
            # if we want to use this
            if axstr.find("xy") == 0 and axstr.find("z") <= 2:
                print(" ... got xyz seq")
                self.Minstr = self.Minstrxyz
                Mcommon1 = True

            for ax in self.seq.keys():
                if ax == "x" and not Mcommon1:
                    print(" ... got x seq")
                    self.Minstr = np.dot(self.Minstr, self.Mx())
                elif ax == "y" and not Mcommon1:
                    print(" ... got y seq")
                    self.Minstr = np.dot(self.Minstr, self.My())
                elif ax == "z" and not Mcommon1:
                    print(" ... got z seq")
                    self.Minstr = np.dot(self.Minstr, self.Mz())
                elif ax == "Rx":
                    print(" ... got Rx seq")
                    self.Minstr = np.dot(self.Minstr, self.Rx())
                elif ax == "Ry":
                    print(" ... got Ry seq")
                    self.Minstr = np.dot(self.Minstr, self.Ry())
                elif ax == "Rz":
                    print(" ... got Rz seq")
                    self.Minstr = np.dot(self.Minstr, self.Rz())

            self.M = np.dot(self.Minstr, self.Mplate)

            # precalculate the inverse as we also need it a lot
            try:
                self.Minv = self.M.I
            except Exception:
                print(
                    "------------------------------ System Matrix singular ---------------------------"
                )
                # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
                self.Minv = np.matrix(
                    [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, -1]]
                )

            try:
                self.Minstrinv = self.Minstr.I
            except Exception:
                print(
                    "------------------------------ Instrument Matrix singular ---------------------------"
                )
                # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
                self.Minstrinv = np.matrix(
                    [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, -1]]
                )

            print(" ... new system matrix:")
            print(self.M)
            print(" ... new inverse system matrix:")
            print(self.Minv)

    def update_Mplatexy(self, Mxy):
        """updates the xy part of the plate calibration"""
        Mxy = np.matrix(Mxy)
        # assign the xy part
        self.Mplate[0:2, 0:2] = Mxy[0:2, 0:2]
        # assign the last row (offsets), notice the difference in col (3x3 vs 4x4)
        #        self.Mplate[0:2,3] = Mxy[0:2,2] # something does not work with this one is a 1x2 the other 2x1 for some reason
        self.Mplate[0, 3] = Mxy[0, 2]
        self.Mplate[1, 3] = Mxy[1, 2]
        # self.Mplate[3,0:4] should always be 0,0,0,1 and should never change

        # update the system matrix so we save calculation time later
        self.update_Msystem()

    def get_Mplatexy(self):
        """returns the xy part of the platecalibration"""
        self.Mplatexy = np.asmatrix(np.identity(3))
        self.Mplatexy[0:2, 0:2] = self.Mplate[0:2, 0:2]
        self.Mplatexy[0, 2] = self.Mplate[0, 3]
        self.Mplatexy[1, 2] = self.Mplate[1, 3]
        return self.Mplatexy

    def get_Mplate_Msystem(self, Mxy):
        """removes Minstr from Msystem to obtain Mplate for alignment"""
        Mxy = np.asarray(Mxy)
        Mglobal = np.asmatrix(np.identity(4))
        Mglobal[0:2, 0:2] = Mxy[0:2, 0:2]
        Mglobal[0, 3] = Mxy[0, 2]
        Mglobal[1, 3] = Mxy[1, 2]

        try:
            Minstrinv = self.Minstr.I
            Mtmp = np.dot(Minstrinv, Mglobal)
            self.Mplatexy = np.asmatrix(np.identity(3))
            self.Mplatexy[0:2, 0:2] = Mtmp[0:2, 0:2]
            self.Mplatexy[0, 2] = Mtmp[0, 3]
            self.Mplatexy[1, 2] = Mtmp[1, 3]

            return self.Mplatexy
        except Exception:
            print(
                "------------------------------ Instrument Matrix singular ---------------------------"
            )
            # use the -1 to signal inverse later --> platexy will then be [x,y,-1]
            self.Minv = np.matrix([[0, 0, 0], [0, 0, 0], [0, 0, -1]])
