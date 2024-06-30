import sys
import re
import json
import time
import numpy as np
import threading
from abc import ABC
from enum import Enum
from dataclasses import dataclass


class EndEffectorType(Enum):
    """Enumeration for different types of end effectors."""

    NO_END_EFFECTOR = 0
    SUCTION_CUP = 1
    GRIPPER = 2


@dataclass
class EndEffectorPins(ABC):
    """Base class representing the pins of the end effector."""

    pass


@dataclass
class AirPumpPins(EndEffectorPins):
    """Represents the pins of the air pump."""

    power: int
    direction: int


# Map end effector types to their respective pin mappings
pin_mapping = {
    EndEffectorType.NO_END_EFFECTOR: None,
    EndEffectorType.GRIPPER: AirPumpPins,
    EndEffectorType.SUCTION_CUP: AirPumpPins,
}


class dobot():
    def __init__(self, config: dict):
        """
        Initializes the dobot object, given a config, which requires the following attributes

        ConfigArgs:
            api_path (str): The path to the dobot api.
            ip (str): The IP address of the robot.
            dashboard_port (int): The port number for the dashboard connection.
            move_port (int): The port number for the move connection.
            error_codes (str): The path to the error code translation file.
            number_of_joints (int): The number of joints in the robot.
            end_effector (int): The type of end effector.
            end_effector_pins (dict): The pins of the end effector.
            end_effector_state (int): The state of the end effector.
            joint_acceleration(int): The joint acceleration value.
            linear_acceleration(int): The linear acceleration value.
            joint_bounds(list): The joint bounds of the robot.
        """
        self._dashboard = None
        self._move = None

        sys.path.append(config["api_path"])
        global DobotApiDashboard, DobotApiMove
        from dobot_api import DobotApiDashboard, DobotApiMove

        self.ip = config["ip"]
        self.identifier = self.ip.split(".")[-1]
        self.dashboard_port = config["dashboard_port"]
        self.move_port = config["move_port"]
        self.error_translation = json.load(open(config["error_codes"], "r"))
        self.error_translation = {int(k): v for k, v in self.error_translation.items()}

        self.number_of_joints = config["number_of_joints"]

        self.end_effector = EndEffectorType(config["end_effector"])
        self.end_effector_pins = pin_mapping[self.end_effector](**config["end_effector_pins"])
        self.end_effector_state = config["end_effector_state"]

        self.dashboard_lock = threading.Lock()

        self.connect()
        self.init(config["joint_acceleration"], config["linear_acceleration"])

        self.joint_bounds = np.array(config["joint_bounds"])

    def connect(self):
        """
        Connects to the robot.

        This function establishes a connection with the robot using the specified IP address and ports.
        It initializes the DobotApiDashboard and DobotApiMove objects for communication with the robot.
        If the connection is successful, it logs a success message. Otherwise, it logs a failure message and raises an exception.

        Raises:
            Exception: If the connection to the robot fails.

        """
        try:
            self.log_robot("Connecting")
            self._dashboard = DobotApiDashboard(self.ip, self.dashboard_port, False)
            self._move = DobotApiMove(self.ip, self.move_port, False)
            self.log_robot("Connection successful")
        except Exception as e:
            self.log_robot("Connection failure")
            raise e

    def init(self, joint_acceleration: int, linear_acceleration: int):
        """
        Initializes the robot by clearing any errors and enabling the robot. (Thread-safe)

        Args:
            joint_acceleration (int): The joint acceleration value.
            linear_acceleration (int): The linear acceleration value.
        """
        with self.dashboard_lock:
            self._dashboard.ClearError()
            time.sleep(0.5)
            self._dashboard.EnableRobot()

        self.set_joint_acceleration(joint_acceleration)
        self.set_linear_acceleration(linear_acceleration)

    def is_alive(self):
        """
        Check if the robot is alive by attempting to get its pose from the dashboard. (Thread-safe)

        Returns:
            bool: True if the robot is alive, False otherwise.
        """
        try:
            with self.dashboard_lock:
                self._dashboard.GetPose()
            return True
        except:
            return False

    def reconnect(self):
        """
        Reconnects to the robot.
        """
        self.log_robot("Connection lost")
        self.log_robot("Trying to reconnect")
        self.disconnect()
        time.sleep(0.5)
        self.connect()
        self.init()

    def disconnect(self):
        """
        Closes the robot connection.
        """
        with self.dashboard_lock:
            self._dashboard.DisableRobot() 
            time.sleep(0.5)
            self._dashboard.close()
        self._move.close()

    def log_robot(self, msg: str):
        """
        Logs a message with the robot identifier.

        Args:
            msg (str): The message to be logged.
        """
        print(f"[DOBOT {self.identifier}] {msg}")

    def clear_error(self):
        """
        Clears the error on the robot. (Thread-safe)

        Note:
            This method requires the robot to be connected and the dashboard to be accessible.
        """
        self.log_robot("Clearing error (" + str(self.error_id) + ")")
        with self.dashboard_lock:
            self._dashboard.ClearError()
            time.sleep(0.5)
            self._dashboard.EnableRobot()

    def set_end_effector(self, end_effector: EndEffectorType):
        """
        Sets the end effector of the robot.

        Args:
            end_effector (EndEffectorType): The end effector type to be set.
        """
        self.end_effector = end_effector
        self.end_effector_pins = pin_mapping[end_effector]
        self.log_robot(f"Setting end effector to {end_effector.name}")

    def set_end_effector_pins(self, values: list):
        """
        Sets the end effector pins of the robot.

        Args:
            values (list): The end effector pin values to be set.
        """
        self.end_effector_pins = pin_mapping[self.end_effector](*values)
        self.log_robot(f"Setting end effector pins to {values}")

    def set_end_effector_state(self, state: int):
        """
        Sets the state of the end effector.

        Args:
            state (int): The state to be set.
        """
        self.end_effector_state = state
        self.log_robot(f"Setting end effector state to {state}")

    def set_digital_output(self, index, value):
        """
        Sets the digital output of the robot.

        Args:
            index (int): The index of the digital output.
            value (int): The value to be set.
        """
        with self.dashboard_lock:
            self._dashboard.DO(int(index), int(value))

    def open_gripper(self):
        """
        Opens the gripper.
        """
        self.set_digital_output(self.end_effector_pins.direction, 1)
        self.set_digital_output(self.end_effector_pins.power, 0)
        time.sleep(0.1)
        self.set_digital_output(self.end_effector_pins.power, 1)

    def close_gripper(self):
        """
        Closes the gripper.
        """
        self.set_digital_output(self.end_effector_pins.direction, 0)
        self.set_digital_output(self.end_effector_pins.power, 0)
        time.sleep(0.1)
        self.set_digital_output(self.end_effector_pins.power, 1)

    def suck(self):
        """
        Turns on the suction cup.
        """
        self.set_digital_output(self.end_effector_pins.direction, 0)
        self.set_digital_output(self.end_effector_pins.power, 0)

    def unsuck(self):
        """
        Turns off the suction cup.
        """
        self.set_digital_output(self.end_effector_pins.direction, 0)
        self.set_digital_output(self.end_effector_pins.power, 1)

    def move_joint_absolute(self, cartesian_coordinates):
        """
        Moves the robot to the specified joint positions.

        Args:
            cartesian_coordinates (tuple): A tuple of canonical coordinates.
        """
        self._move.MovJ(*cartesian_coordinates)
        self._move.Sync()

    def move_linear_absolute(self, cartesian_coordinates):
        """
        Moves the robot to the specified linear coordinates.

        Args:
            cartesian_coordinates (tuple): A tuple of canonical coordinates.
        """
        self._move.MovL(*cartesian_coordinates)
        self._move.Sync()

    def move_joint_relative(self, movement):
        """
        Moves the robot relative to the current joint positions.

        Args:
            movement (tuple): A tuple of relative joint movements.
        """
        self._move.RelMovJ(*movement)
        self._move.Sync()

    def move_linear_relative(self, movement):
        """
        Moves the robot relative to the current joint positions linearly.

        Args:
            movement (tuple): A tuple of relative joint movements.
        """
        self._move.RelMovL(*movement)
        self._move.Sync()

    def bound_movement(self, movement: list) -> list:
        """
        Bound the movement of the robot in an attempt to prevent invalid movements.

        Args:
            movement (list): The movement to be bounded.

        Returns:
            list: The bounded movement.

        Raises:
            Exception: If no angles are available.
        """

        current_angles = self.angles.copy()

        if current_angles.size:
            attempted_angles = current_angles + movement
            attempted_angles = np.clip(
                attempted_angles, self.joint_bounds[:, 0], self.joint_bounds[:, 1]
            )
            return attempted_angles - current_angles
        else:
            raise Exception("No angles available")

    def nonblocking_move(self, func, params) -> bool:
        """
        Executes the given function with the provided parameters in a non-blocking manner. Which means checking and potentially
        clearing for robot errors.

        Args:
            func (callable): The function to be executed.
            params (tuple): The parameters to be passed to the function.

        Returns:
            bool: True if the function executed successfully without any errors, False otherwise.
        """
        func(params)
        if len(self.error_id):
            self.log_robot(f"Invalid movement [{self.error_id}]")
            self.clear_error()
            return False
        return True

    def set_joint_speed(self, speed):
        """
        Sets the joint speed of the robot. (Thread-safe)

        Args:
            speed (int): The desired joint speed.
        """
        self.log_robot(f"Setting joint speed to {speed}")
        with self.dashboard_lock:
            self._dashboard.SpeedJ(int(speed))

    def set_linear_speed(self, speed):
        """
        Sets the linear speed of the robot. (Thread-safe)

        Args:
            speed (int): The desired linear speed.
        """
        self.log_robot(f"Setting linear speed to {speed}")
        with self.dashboard_lock:
            self._dashboard.SpeedL(int(speed))

    def set_joint_acceleration(self, acceleration):
        """
        Sets the joint acceleration of the robot. (Thread-safe)

        Args:
            acceleration (int): The desired joint acceleration.
        """
        self.log_robot(f"Setting joint acceleration to {acceleration}")
        with self.dashboard_lock:
            self._dashboard.AccJ(int(acceleration))

    def set_linear_acceleration(self, acceleration):
        """
        Sets the linear acceleration of the robot. (Thread-safe)

        Args:
            acceleration (int): The desired linear acceleration value.
        """
        self.log_robot(f"Setting linear acceleration to {acceleration}")
        with self.dashboard_lock:
            self._dashboard.AccL(int(acceleration))

    @staticmethod
    def extract_metavalues(s):
        """
        Extracts the return value and method name from the dobot call.

        Args:
            s (str): The input string.

        Returns:
            tuple: A tuple containing the return value and method name extracted from the input string.
        """
        return_value = int(s.split(",")[0])
        method_name = re.search(r"\b\w+\b(?=\(\);)", s).group()

        return return_value, method_name

    @staticmethod
    def extract_error_codes(s):
        """
        Extracts error codes from the dobot call.

        Args:
            s (str): The input string.

        Returns:
            list: A list of error codes extracted from the input string.
        """
        error_codes_str = s[s.find("["): s.rfind("]") + 1]
        error_codes = json.loads(error_codes_str)

        error_codes = [item for sublist in error_codes for item in sublist]
        return error_codes

    def extract_pose(self, s):
        """
        Extracts the pose from the dobot call.

        Args:
            s (str): The string representation of the pose.

        Returns:
            tuple: A tuple containing the extracted pose values.
        """
        return np.fromstring(s[s.find("{") + 1: s.find("}")], sep=",")[
               : self.number_of_joints
               ]

    def extract_angles(self, s):
        return np.fromstring(s[s.find("{") + 1: s.find("}")], sep=",")[
               : self.number_of_joints
               ]

    @property
    def pose(self):
        """
        Returns the pose of the robot in [x, y, z, r] format. (Thread-safe)

        Returns:
            numpy.ndarray: The pose of the robot as a numpy array.

        Raises:
            Exception: If there is an error getting the pose.
        """
        try:
            with self.dashboard_lock:
                result = self._dashboard.GetPose()

            return_value, method_name = self.extract_metavalues(result)

            if return_value == 0 and method_name == "GetPose":
                pose = self.extract_pose(result)
                return pose
            else:
                self.log_robot(f"Error extracting pose {result}")
                return np.array([0, 0, 0, 0])
        except Exception as e:
            self.log_robot(f"Error getting pose {e}")
            return np.array([0, 0, 0, 0])

    @property
    def angles(self):
        """
        Returns the angles of the robot in [j1, j2, j3, j4] format. (Thread-safe)

        Returns:
            numpy.ndarray: An array containing the angles of the robot in [j1, j2, j3, j4] format.

        Raises:
            Exception: If there is an error getting the angles.
        """
        try:
            with self.dashboard_lock:
                result = self._dashboard.GetAngle()

            return_value, method_name = self.extract_metavalues(result)
            if return_value == 0 and method_name == "GetAngle":
                angles = self.extract_angles(result)
                return angles
            else:
                self.log_robot(f"Error extracting angles {result}")
                return np.array([0, 0, 0, 0])
        except Exception as e:
            self.log_robot(f"Error getting angles {e}")
            return np.array([0, 0, 0, 0])

    @property
    def error_id(self):
        """
        Retrieves the error codes and their translations from the robot's dashboard. (Thread-safe)

        Returns:
            A list of error code translations. If there are no error codes or an error occurs during retrieval,
            an empty list is returned.
        """

        try:
            with self.dashboard_lock:
                result = self._dashboard.GetErrorID()

            return_value, method_name = self.extract_metavalues(result)

            if return_value == 0 and method_name == "GetErrorID":
                translations = []
                for error_code in self.extract_error_codes(result):
                    if error_code in self.error_translation:
                        translations.append(self.error_translation[error_code])
                    else:
                        translations.append(f"Unknown error {error_code}")
                return translations
            else:
                self.log_robot(f"Error extracting error codes {result}")
        except json.decoder.JSONDecodeError:
            self.log_robot(f"Error in JSON parsing")
            return []
        except Exception as e:
            self.log_robot(f"Error getting error id {e}")
            print("Result", result)
