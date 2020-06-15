import sys
import os
import numpy as np
import json
import time

if __package__:
    # can import directly in package mode
    print("importing config vars from package path")
else:
    # interactive kernel mode requires path manipulation
    cwd = os.getcwd()
    pwd = os.path.dirname(cwd)
    if os.path.basename(pwd) == "HELAO":
        sys.path.insert(0, pwd)
    if pwd in sys.path or os.path.basename(cwd) == "HELAO":
        print("importing config vars from sys.path")
    else:
        raise ModuleNotFoundError("unable to find config vars, current working directory is {}".format(cwd))

from config.config import *

if GALIL_SIMULATE:
    import gclib_simulate as gclib
else:
    import gclib


setupd = GALIL_SETUPD


class galil:
    def __init__(self):
        # if this is the main instance let us make a galil connection
        self.g = gclib.py()
        print("gclib version:", self.g.GVersion())
        self.g.GOpen("%s --direct -s ALL" % (setupd["galil_ip_str"]))
        print(self.g.GInfo())
        self.c = self.g.GCommand  # alias the command callable
        self.cycle_lights = False

    def motor_move(self, x_mm, axis, speed, mode, stopping=True):
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
        # the server call would look like:
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=relative
        # http://127.0.0.1:8001/motor/set/move?x_mm=-20&axis=x&mode=absolute

        # first we check if we have the right axis specified
        if axis in setupd["axis_id"].keys():
            ax = setupd["axis_id"][axis]
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
        try:
            print(setupd["count_to_mm"][ax])
            float_counts = (
                x_mm / setupd["count_to_mm"][ax]
            )  # calculate float dist from steupd
            print(setupd["count_to_mm"][ax])

            counts = int(np.floor(float_counts))  # we can only mode full counts
            # save and report the error distance
            error_distance = setupd["count_to_mm"][ax] * (float_counts - counts)

            # check if a speed was upplied otherwise set it to standart
            if speed == None:
                speed = setupd["def_speed_count_sec"]
            else:
                speed = int(np.floor(speed))

            if speed > setupd["max_speed_count_sec"]:
                speed = setupd["max_speed_count_sec"]
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
                raise cmd_exception
            if stopping:
                cmd_seq = ["AB", "MO", "SH", "SP{}={}".format(ax, speed)]
            else:
                cmd_seq = ["SP{}={}".format(ax, speed)]
            if mode == "relative":
                cmd_seq.append("PR{}={}".format(ax, counts))
            if mode == "homing":
                cmd_seq.append("HM{}".format(ax))
            if mode == "absolute":
                # now we want an abolute position
                # identify which axis we are talking about
                axlett = {l: i for i, l in enumerate(setupd["axlett"])}
                cmd_str = "PA " + ",".join(
                    str(0) if ax != lett else str(counts) for lett in setupd["axlett"]
                )
                cmd_seq.append(cmd_str)
            cmd_seq.append("BG{}".format(ax))

            ret = ""
            for cmd in cmd_seq:
                _ = self.c(cmd)
                ret.join(_)
            return {
                "moved_axis": ax,
                "speed": speed,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": error_distance,
                "err_code": 0,
                "counts": counts,
            }
        except:
            return {
                "moved_axis": None,
                "speed": None,
                "accepted_rel_dist": None,
                "supplied_rel_dist": x_mm,
                "err_dist": None,
                "err_code": "motor",
            }

    def motor_move_live(self, x_mm, axis, speed, mode):
        # this function moves the motor by a set amount of milimeters
        # you have to specify the axis,
        # if no axis is specified this function throws an error
        # if no speed is specified we use the default slow speed
        # as specified in the setupdictm

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
        if axis in setupd["axis_id"].keys():
            ax = setupd["axis_id"][axis]
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
        try:
            float_counts = (
                x_mm / setupd["count_to_mm"][ax]
            )  # calculate float dist from steupd
            counts = int(np.floor(float_counts))  # we can only mode full counts
            # save and report the error distance
            error_distance = setupd["count_to_mm"][ax] * (float_counts - counts)

            # check if a speed was upplied otherwise set it to standart
            if speed == None:
                speed = setupd["def_speed_count_sec"]
            else:
                speed = int(np.floor(speed))

            if speed > setupd["max_speed_count_sec"]:
                speed = setupd["max_speed_count_sec"]
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
                raise cmd_exception

            cmd_seq = ["AB", "MO", "SH", "SP{}={}".format(ax, speed)]
            if mode == "relative":
                cmd_seq.append("PR{}={}".format(ax, counts))
            if mode == "homing":
                cmd_seq.append("HM{}".format(ax))
            if mode == "absolute":
                # now we want an abolute position
                # identify which axis we are talking about
                axlett = {l: i for i, l in enumerate(setupd["axlett"])}
                cmd_str = "PA " + ",".join(
                    str(0) if ax != lett else str(counts) for lett in setupd["axlett"]
                )
                cmd_seq.append(cmd_str)
            cmd_seq.append("BG{}".format(ax))

            ret = ""
            for cmd in cmd_seq:
                _ = self.c(cmd)
                ret.join(_)
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
        try:
            self.g.GClose()  # don't forget to close connections!
        except gclib.GclibError as e:
            return {"connection": {"Unexpected GclibError:", e}}
        return {"connection": "motor_offline"}

    def query_all_axis_positions(self):
        # this queries all axis positions
        # example: query_all_axis_positions()
        # a server call should look like
        # http://127.0.0.1:8000/motor/query/positions
        # first query the actual position
        ret = self.c("TP")  # query position of all axis
        # now we need to map these outputs to the ABCDEFG... channels
        # and then map that to xyz so it is humanly readable

        inv_axis_id = {d: v for v, d in setupd["axis_id"].items()}
        ax_abc_to_xyz = {l: inv_axis_id[l] for i, l in enumerate(setupd["axlett"])}
        pos = {
            axl: int(r) * setupd["count_to_mm"][axl]
            for axl, r in zip(setupd["axlett"], ret.split(", "))
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

    def query_moving(self,):
        # this function queries the galil motor controller if any of
        # it's motors are moving if so it returns moving as a
        # motor_status otherwise stopped. Stopping codes can mean different things
        # here we just want to know if is is moving or not

        # a server call would look like:
        # http://127.0.0.1:8000/motor/query/position?axis=x
        ret = self.c("SC")
        inv_axis_id = {d: v for v, d in setupd["axis_id"].items()}
        ax_abc_to_xyz = {l: inv_axis_id[l] for i, l in enumerate(setupd["axlett"])}
        for axl, r in zip(setupd["axlett"], ret.split(", ")):
            if int(r) == 0:
                return {"motor_status": "moving"}
        return {"motor_status": "stopped"}

    def motor_off(self, axis):
        # sometimes it is useful to turn the motors off for manual alignment
        # this function does exactly that
        # It then returns the status
        # and the current position of all motors

        # an example would be:
        # http://127.0.0.1:8000/motor/stop

        if axis in setupd["axis_id"].keys():
            ax = setupd["axis_id"][axis]
        else:
            ret = self.query_moving()
            ret.update(self.query_all_axis_positions())
            return ret

        cmd_seq = ["AB", "MO{}".format(ax)]
        for cmd in cmd_seq:
            _ = self.c(cmd)
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
        if axis in setupd["axis_id"].keys():
            ax = setupd["axis_id"][axis]
        else:
            ret = self.query_moving()
            ret.update(self.query_all_axis_positions())
            return ret
        cmd_seq = ["AB", "SH{}".format(ax)]
        for cmd in cmd_seq:
            _ = self.c(cmd)
        ret = self.query_moving()
        ret.update(self.query_all_axis_positions())
        return ret

    def motor_stop(self):
        # this immediately stopps all motions turns off themotors for a short
        # time and then turns them back on. It then returns the status
        # and the current position of all motors
        # a server example would be
        # http://127.0.0.1:8000/motor/off?axis=x
        cmd_seq = ["AB", "MO", "SH"]
        for cmd in cmd_seq:
            _ = self.c(cmd)
        ret = self.query_moving()
        ret.update(self.query_all_axis_positions())
        return ret

    def read_analog_in(self, port: int):
        # this reads the value of an analog in port
        # http://127.0.0.1:8000/
        ret = self.c("MG @AN[{}]".format(port))
        return {"port": port, "value": ret, "type": "analog_in"}

    def read_digital_in(self, port: int):
        # this reads the value of a digital in port
        # http://127.0.0.1:8000/
        ret = self.c("MG @IN[{}]".format(port))
        return {"port": port, "value": ret, "type": "digital_in"}

    def read_digital_out(self, port: int):
        # this reads the value of an digital out port i.e. what is
        # actuallybeing put out (for checking)
        # http://127.0.0.1:8000/
        ret = self.c("MG @IN[{}]".format(port))
        return {"port": port, "value": ret, "type": "digital_out"}

    def set_analog_out(self, handle: int, module: int, bitnum: int, value: float):
        # this is essentially a placeholder for now since the DMC-4143 does not support
        # analog out butI believe it is worthwhile to have this in here for the RIO
        # Handle num is A-H and must be on port 502 for the modbus commons
        # module is the position of the module from 1 to 16
        # bitnum is the IO point in the module from 1-4
        # the fist value n_0
        n_0 = handle * 1000 + (module - 1) * 4 + bitnum
        ret = self.c("AO {},{}".format(port, value))
        return {"port": port, "value": value, "type": "analog_out"}

    def digital_out_on(self, port: int):
        ret = self.c("SB {}".format(port))
        return {
            "port": port,
            "value": self.read_digital_out(port),
            "type": "digital_out",
        }

    def digital_out_off(self, port: int):
        ret = self.c("CB {}".format(port))
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
        self.g.GClose()
        return {"shutdown"}
