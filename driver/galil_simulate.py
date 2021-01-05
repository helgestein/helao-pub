""" A device class for the Galil motion controller, used by a FastAPI server instance.

The 'galil' device class simulates the underlying motion and I/O functions provided by
'gclib'. The simulation class does not depend on the external 'gclib' library.
"""

#import sys
#import os
import numpy as np
import json
import time
from collections import defaultdict


class cmd_exception(ValueError):
    def __init__(self, arg):
        self.args = arg


class galil:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        # if this is the main instance let us make a galil connection
        # self.g = gclib.py()
        print("gclib version:", "SIMULATE")
        # self.g.GOpen("%s --direct -s ALL" % (self.config_dict["galil_ip_str"]))
        # print(self.g.GInfo())
        # self.c = self.g.GCommand  # alias the command callable
        self.cycle_lights = False

        # setup time variables to simulate moving
        #   set future stop_time with motor_move (now + seconds)
        #   query and motor_move methods need to check if now > stop_time
        self.start_time = time.time()
        self.stop_time = time.time()

        # setup dict to hold positions
        #  start all axes at 0 position
        #  GALIL_self.config_dict does not have axis limits!!
        self.axlast = {ch: 0 for ch in 'ABCDEFGH'}
        self.axdict = {ch: 0 for ch in 'ABCDEFGH'}

        # setup dict to hold I/O
        self.aidict = defaultdict(float)
        self.aodict = defaultdict(float)
        self.didict = defaultdict(int)
        self.doflag = defaultdict(int)

    # single axis motion, executes after building command string
    def motor_move(self, multi_x_mm, multi_axis, speed, mode, stopping=True):
        # this function moves the motor by a set amount of millimeters
        # you have to specify the axis,
        # if no axis is specified this function throws an error
        # if no speed is specified we use the default slow speed
        # as specified in the self.config_dictict

        # example: move the motor 5mm to the positive direction:
        # motor_move(5,'x')
        # example: move the motor to absolute 0 mm
        # motor_move(5,'x',mode='absolute')
        # home the motor at low speed (the distance is not used)
        # motor_move(5,'x',mode='homing',speed=10000)
        # the server call would look like:
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=relative
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=absolute

        # convert single axis move to list        
        if type(multi_x_mm) is not list:
            multi_axis = [multi_axis]
            multi_x_mm = [multi_x_mm]
        
        # return value arrays for multi axis movement
        ret_moved_axis = []
        ret_speed = []
        ret_accepted_rel_dist = []
        ret_supplied_rel_dist = []
        ret_err_dist = []
        ret_err_code = []
        ret_counts = []
        
        for x_mm, axis in zip(multi_x_mm, multi_axis):
       
        
            # first we check if we have the right axis specified
            if axis in self.config_dict["axis_id"].keys():
                ax = self.config_dict["axis_id"][axis]
    
            else:
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(None)
                ret_err_code.append("setup")
                ret_counts.append(None)
                continue
                
            # check if the motors are moving if so return an error message
            # recalculate the distance in mm into distance in counts
            if time.time() < self.stop_time or stopping is False:
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(None)
                ret_err_code.append("motor_in_motion")
                ret_counts.append(None)
                continue
    
            try:
                # print(self.config_dict["count_to_mm"][ax])
                float_counts = (
                    x_mm / self.config_dict["count_to_mm"][ax]
                )  # calculate float dist from self.config_dict
                # print(self.config_dict["count_to_mm"][ax])
    
                counts = int(np.floor(float_counts))  # we can only mode full counts
                print(counts)
                # save and report the error distance
                error_distance = self.config_dict["count_to_mm"][ax] * (float_counts - counts)
    
                # check if a speed was supplied otherwise set it to standard
                if speed == None:
                    speed = self.config_dict["def_speed_count_sec"]
                else:
                    speed = int(np.floor(speed))
    
                if speed > self.config_dict["max_speed_count_sec"]:
                    speed = self.config_dict["max_speed_count_sec"]
                self._speed = speed
            except:
                # something went wrong in the numerical part so we give that as feedback
                ret_moved_axis.append(None)
                ret_speed.append(None)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(None)
                ret_err_code.append("numerical")
                ret_counts.append(None)
                continue

            if True:
                # the logic here is that we assemble a command sequence
                # here we decide if we move relative, home, or move absolute
                if mode not in ["relative", "absolute", "homing"]:
                    raise cmd_exception("mode not one of {'relative', 'absolute', 'homing'}")
    
                if stopping:  # interrupt current motion
                    self.start_time = time.time()
                    self.stop_time = time.time()
    
                # else:  # if not stopping, set speed?, condition seems unrelated
                    # cmd_seq = ["SP{}={}".format(ax, speed)]
    
                if mode == "relative":
                    # cmd_seq.append("PR{}={}".format(ax, counts))
                    dist = counts
                    self.axlast[ax] = self.axdict[ax]
                    self.axdict[ax] += counts
    
                if mode == "homing":
                    # cmd_seq.append("HM{}".format(ax))
                    dist = np.abs(self.axdict[ax])
                    self.axlast[ax] = self.axdict[ax]
                    self.axdict[ax] = 0
    
                if mode == "absolute":
                    # now we want an absolute position
                    # identify which axis we are talking about
                    # axlett = {l: i for i, l in enumerate(self.config_dict["axlett"])}
                    # cmd_str = "PA " + ",".join(
                    #     str(0) if ax != lett else str(counts) for lett in self.config_dict["axlett"]
                    # )
                    # cmd_seq.append(cmd_str)
                    dist = np.abs(counts - self.axdict[ax])
                    self.axlast[ax] = self.axdict[ax]
                    self.axdict[ax] = counts
    
                # cmd_seq.append("BG{}".format(ax))
    
                motion_time = 1.0*dist/speed
                self.start_time = time.time()
                self.stop_time = time.time() + motion_time
    
                # ret = ""
                # for cmd in cmd_seq:
                #     _ = self.c(cmd)
                #     ret.join(_)
    
                ret_moved_axis.append(ax)
                ret_speed.append(speed)
                ret_accepted_rel_dist.append(None)
                ret_supplied_rel_dist.append(x_mm)
                ret_err_dist.append(error_distance)
                ret_err_code.append(0)
                ret_counts.append(counts)
                continue
            # except:
            #     return {
            #         "moved_axis": None,
            #         "speed": None,
            #         "accepted_rel_dist": None,
            #         "supplied_rel_dist": x_mm,
            #         "err_dist": None,
            #         "err_code": "motor",
            #     }
        
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

    def motor_move_live(self, x_mm, axis, speed, mode):
        # this function moves the motor by a set amount of millimeters
        # you have to specify the axis,
        # if no axis is specified this function throws an error
        # if no speed is specified we use the default slow speed
        # as specified in the self.config_dictict

        # example: move the motor 5mm to the positive direction:
        # motor_move(5,'x')
        # example: move the motor to absolute 0 mm
        # motor_move(5,'x',mode='absolute')
        # home the motor at low speed (the distance is not used)
        # motor_move(5,'x',mode='homing',speed=10000)
        # the server call would look like:
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=relative
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=absolute

        # first we check if we have the right axis specified
        if axis in self.config_dict["axis_id"].keys():
            ax = self.config_dict["axis_id"][axis]
        else:
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": None,
                "err_code": "setup",
            }

        # check if the motors are moving if so return an error message
        # recalculate the distance in mm into distance in counts
        if time.time() < self.stop_time:
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": None,
                "err_code": "motor_in_motion",
            }

        try:
            float_counts = (
                x_mm / self.config_dict["count_to_mm"][ax]
            )  # calculate float dist from self.config_dict
            counts = int(np.floor(float_counts))  # we can only mode full counts
            # save and report the error distance
            error_distance = self.config_dict["count_to_mm"][ax] * (float_counts - counts)

            # check if a speed was supplied otherwise set it to standard
            if speed == None:
                speed = self.config_dict["def_speed_count_sec"]
            else:
                speed = int(np.floor(speed))

            if speed > self.config_dict["max_speed_count_sec"]:
                speed = self.config_dict["max_speed_count_sec"]
            self._speed = speed
        except:
            # something went wrong in the numerical part so we give that as feedback
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": None,
                "err_code": "numerical",
            }
        try:
            # the logic here is that we assemble a command sequence
            # here we decide if we move relative, home, or move absolute
            if mode not in ["relative", "absolute", "homing"]:
                raise cmd_exception("mode not one of {'relative', 'absolute', 'homing'}")

            # cmd_seq = ["AB", "MO", "SH", "SP{}={}".format(ax, speed)]
            if mode == "relative":
                # cmd_seq.append("PR{}={}".format(ax, counts))
                dist = counts
                self.axlast[ax] = self.axdict[ax]
                self.axdict[ax] += counts

            if mode == "homing":
                # cmd_seq.append("HM{}".format(ax))
                dist = np.abs(self.axdict[ax])
                self.axlast[ax] = self.axdict[ax]
                self.axdict[ax] = 0

            if mode == "absolute":
                # now we want an absolute position
                # identify which axis we are talking about
                # axlett = {l: i for i, l in enumerate(self.config_dict["axlett"])}
                # cmd_str = "PA " + ",".join(
                #     str(0) if ax != lett else str(counts) for lett in self.config_dict["axlett"]
                # )
                # cmd_seq.append(cmd_str)
                dist = np.abs(counts - self.axdict[ax])
                self.axlast[ax] = self.axdict[ax]
                self.axdict[ax] = counts

            # cmd_seq.append("BG{}".format(ax))

            # ret = ""
            # for cmd in cmd_seq:
            #     _ = self.c(cmd)
            #     ret.join(_)

            motion_time = 1.0 * dist / speed
            self.start_time = time.time()
            self.stop_time = time.time() + motion_time

            while self.query_moving()["motor_status"] == "moving":
                d = {
                    "moved_axis": ax,
                    "speed": speed,
                    "accepted_rel_dist": None,
                    "supplied_rel_dist": x_mm,
                    "err_dist": error_distance,
                    "err_code": 0,
                    "position": self.query_all_axis_positions(),
                }
                d = json.dumps(d)
                yield d
            d = {
                "moved_axis": ax,
                "speed": speed,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": error_distance,
                "err_code": 0,
                "position": self.query_all_axis_positions(),
            }
            d = json.dumps(d)
            yield d
        except:
            d = {
                "moved_axis": ax,
                "speed": speed,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": error_distance,
                "err_code": 0,
                "position": self.query_all_axis_positions(),
            }
            d = json.dumps(d)
            yield d

    def motor_disconnect(self):
        # try:
        #     self.g.GClose()  # don't forget to close connections!
        # except gclib.GclibError as e:
        #     return {"connection": {"Unexpected GclibError:", e}}
        return {"connection": "motor_offline"}

    def query_all_axis_positions(self):
        # this queries all axis positions
        # example: query_all_axis_positions()
        # a server call should look like
        # http://127.0.0.1:8000/motor/query/positions
        # first query the actual position
        # ret = self.c("TP")  # query position of all axis
        if self.stop_time == self.start_time or time.time() >= self.stop_time:
            elapsed_frac = 1
        else:
            elapsed_frac = (time.time() - self.start_time) / (self.stop_time - self.start_time)
        ret = [self.axdict[k] - (self.axdict[k] - self.axlast[k]) * (1 - elapsed_frac) for k in 'ABCDEFGH']
        # now we need to map these outputs to the ABCDEFG... channels
        # and then map that to xyz so it is humanly readable

        inv_axis_id = {d: v for v, d in self.config_dict["axis_id"].items()}
        ax_abc_to_xyz = {l: inv_axis_id[l] for i, l in enumerate(self.config_dict["axlett"])}
        pos = {
            axl: int(r) * self.config_dict["count_to_mm"][axl]
            for axl, r in zip(self.config_dict["axlett"], ret)
        }
        # return the results through calculating things into mm
        return {ax_abc_to_xyz[k]: p for k, p in pos.items()}

    def query_axis(self, axis):
        # this only queries the position of a single axis
        # server example:
        # http://127.0.0.1:8000/motor/query/position?axis=x
        q = self.query_all_axis_positions()
        if axis in q.keys():
            return {"ax": axis, "position": q[axis]}
        else:
            return {"ax": None, "position": None}

    def query_moving(self):
        # this function queries the galil motor controller if any of
        # it's motors are moving if so it returns moving as a
        # motor_status otherwise stopped. Stopping codes can mean different things
        # here we just want to know if is is moving or not

        # a server call would look like:
        # http://127.0.0.1:8000/motor/query/position?axis=x
        # ret = self.c("SC")

        # inv_axis_id = {d: v for v, d in self.config_dict["axis_id"].items()}
        # ax_abc_to_xyz = {l: inv_axis_id[l] for i, l in enumerate(self.config_dict["axlett"])}
        # for axl, r in zip(self.config_dict["axlett"], ret):
        #     if int(r) == 0:
        if time.time() < self.stop_time:
            return {"motor_status": "moving"}
        return {"motor_status": "stopped"}

    def motor_off(self, axis):
        # sometimes it is useful to turn the motors off for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors

        # an example would be:
        # http://127.0.0.1:8000/motor/stop

        if axis in self.config_dict["axis_id"].keys():
            ax = self.config_dict["axis_id"][axis]
        else:
            ret = self.query_moving()
            ret.update(self.query_all_axis_positions())
            return ret

        # cmd_seq = ["AB", "MO{}".format(ax)]
        # for cmd in cmd_seq:
        #     _ = self.c(cmd)
        ret = self.query_moving()
        ret.update(self.query_all_axis_positions())
        return ret

    def motor_on(self, axis):
        # sometimes it is useful to turn the motors back on for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors
        # server example
        # http://127.0.0.1:8000/motor/on?axis=x
        if axis in self.config_dict["axis_id"].keys():
            ax = self.config_dict["axis_id"][axis]
        else:
            ret = self.query_moving()
            ret.update(self.query_all_axis_positions())
            return ret
        # cmd_seq = ["AB", "SH{}".format(ax)]
        # for cmd in cmd_seq:
        #     _ = self.c(cmd)
        ret = self.query_moving()
        ret.update(self.query_all_axis_positions())
        return ret

    def motor_stop(self):
        # this immediately stops all motions turns off the motors for a short
        # time and then turns them back on. It then returns the status
        # and the current position of all motors
        # a server example would be
        # http://127.0.0.1:8000/motor/off?axis=x
        # cmd_seq = ["AB", "MO", "SH"]
        # for cmd in cmd_seq:
        #     _ = self.c(cmd)
        ret = self.query_moving()
        if self.stop_time == self.start_time or time.time() >= self.stop_time:
            elapsed_frac = 1
        else:
            elapsed_frac = (time.time() - self.start_time) / (self.stop_time - self.start_time)
        for k in 'ABCDEFGH':
            self.axdict[k] = self.axdict[k] - (self.axdict[k] - self.axlast[k]) * (1 - elapsed_frac)
        self.start_time = time.time()
        self.stop_time = time.time()
        ret.update(self.query_all_axis_positions())
        return ret

    def read_analog_in(self, port: int):
        # this reads the value of an analog in port
        # http://127.0.0.1:8000/
        # ret = self.c("MG @AN[{}]".format(port))
        ret = np.random.random()
        return {"port": port, "value": ret, "type": "analog_in"}

    def read_digital_in(self, port: int):
        # this reads the value of a digital in port
        # http://127.0.0.1:8000/
        ret = np.random.randint(2)
        return {"port": port, "value": ret, "type": "digital_in"}

    def read_digital_out(self, port: int):
        # this reads the value of an digital out port i.e. what is
        # actually being put out (for checking)
        # http://127.0.0.1:8000/
        # ret = self.c("MG @IN[{}]".format(port))
        ret = self.doflag[port]
        return {"port": port, "value": ret, "type": "digital_out"}

    def set_analog_out(self, handle: int, module: int, bitnum: int, value: float):
        # this is essentially a placeholder for now since the DMC-4143 does not support
        # analog out butI believe it is worthwhile to have this in here for the RIO
        # Handle num is A-H and must be on port 502 for the modbus commons
        # module is the position of the module from 1 to 16
        # bitnum is the IO point in the module from 1-4
        # the fist value n_0
        n_0 = handle * 1000 + (module - 1) * 4 + bitnum
        # ret = self.c("AO {},{}".format(port, value))
        self.aodict[port] = value
        return {"port": port, "value": value, "type": "analog_out"}

    def digital_out_on(self, port: int):
        # ret = self.c("SB {}".format(port))
        self.doflag[port] = 1
        return {
            "port": port,
            "value": self.read_digital_out(port),
            "type": "digital_out",
        }

    def digital_out_off(self, port: int):
        # ret = self.c("CB {}".format(port))
        self.doflag[port] = 0
        return {
            "port": port,
            "value": self.read_digital_out(port),
            "type": "digital_out",
        }

    def infinite_digital_cycles(self, on_time=0.2, off_time=0.2, port=0, init_time=0):
        self.cycle_lights = True
        time.sleep(init_time)
        while self.cycle_lights:
            self.digital_out_on(port)
            time.sleep(on_time)
            self.digital_out_off(port)
            time.sleep(off_time)
        return {
            "port": port,
            "value": "ran_infinite_light_cycles",
            "type": "digital_out",
        }

    def break_infinite_digital_cycles(
        self, on_time=0.2, off_time=0.2, port=0, init_time=0
    ):
        self.cycle_lights = False

    def shutdown_event(self):
        # this gets called when the server is shut down or reloaded to ensure a clean
        # disconnect ... just restart or terminate the server
        self.motor_stop()
        # self.g.GClose()
        return {"shutdown"}
