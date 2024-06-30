import sys
import clr
import time
import re
import json 
import time
import threading
import numpy as np

# Add absolute paths to sys.path
sys.path.append(r'C:/Users/juliu/helao-dev')
sys.path.append(r'C:/Users/juliu/helao-dev/config')  # Assuming config.py is directly in the config folder

# Import modules using absolute paths 
from config import config
from utils import MemoryType, MotionType, EndEffectorPins, EndEffectorType, pin_mapping
from dobot_api import DobotApiDashboard, DobotApiMove

class dobot():
    """
    A class representing a robot interface.

    Attributes:
        robot_ip (str): The IP address of the robot.
        dashboard_port (int): The port number for the dashboard connection.
        move_port (int): The port number for the move connection.
        number_of_joints (int): The number of joints in the robot.
        print_function (callable): The function used for printing log messages.
        end_effector (EndEffectorType): The end effector type of the robot.
        end_effector_pins (EndEffectorPins): The end effector pins of the robot.
        end_effector_state (int): The state of the end effector.

    Methods:
        __init__: Initializes the RobotInterface object.
        connect_robot: Connects to the robot.
        init_robot: Initializes the robot.
        reconnect: Reconnects to the robot.
        close_robot: Closes the robot connection.
        move_joint_absolute: Moves the robot to the specified joint coordinates.
        move_linear_absolute: Moves the robot to the specified linear coordinates.
        move_joint_relative: Moves the robot relative to the current joint coordinates.
        move_linear_relative: Moves the robot relative to the current linear coordinates.
        robot_is_alive: Checks if the robot is alive.
        set_joint_speed: Sets the joint speed of the robot.
        set_linear_speed: Sets the linear speed of the robot.
        set_joint_acceleration: Sets the joint acceleration of the robot.
        set_linear_acceleration: Sets the linear acceleration of the robot.
        log_robot: Logs a message with the robot identifier.
        clear_error: Clears the error on the robot.
        set_end_effector: Sets the end effector of the robot.
        set_end_effector_pins: Sets the end effector pins of the robot.
        set_end_effector_state: Sets the state of the end effector.
        nonblocking_move: Performs a non-blocking move operation on the robot.
        extract_metavalues: Extracts the return value and method name from a string.
        extract_error_codes: Extracts the error codes from a string.
        extract_pose: Extracts the pose from a string.
        extract_angles: Extracts the angles from a string.
        pose: Property that returns the current pose of the robot.
        angles: Property that returns the current angles of the robot.
        error_id: Property that returns the error codes of the robot.
        replay: Replays a sequence of robot movements.
    """
#    def __init__(self,config):
#        self.port = config['port']
#        self.dllpath = config['dll']
#        self.dllconfigpath = config['dllconfig']
#        clr.AddReference(self.dllpath)
#        import CClassLStep
#        self.LS = CClassLStep.LStep() #.LSX_CreateLSID(0)
#        self.connected = False
#        self.connect()
#        self.LS.SetVel(config['vx'],config['vy'],config['vz'],0)
    
    def __init__(
        self,
        robot_ip: str = "192.168.1.6",
        dashboard_port: int = 29999,
        move_port: int = 30003,
        number_of_joints: int = 4,
        print_function: callable = print,
        end_effector: EndEffectorType = EndEffectorType.NO_END_EFFECTOR,
        end_effector_pins: EndEffectorPins = None,
        end_effector_state: int = 0,
    ):
        """
        Initializes the RobotI      nterface object.

        Args:
            robot_ip (str): The IP address of the robot.
            dashboard_port (int): The port number for the dashboard connection.
            move_port (int): The port number for the move connection.
            number_of_joints (int): The number of joints in the robot.
            print_function (callable): The function used for printing log messages.
        """
        self._dashboard = None
        self._move = None

        self.dashboard_lock = threading.Lock()

        self.robot_ip = robot_ip
        self.identifier = robot_ip.split(".")[-1]
        self.dashboard_port = dashboard_port
        self.move_port = move_port
        self.error_translation = json.load(
            open("driver/error_codes.json", "r"),
        )
        self.error_translation = {int(k): v for k, v in self.error_translation.items()}

        self.number_of_joints = number_of_joints

        self.print_function = print_function

        self.end_effector = end_effector
        self.end_effector_pins = end_effector_pins
        self.end_effector_state = end_effector_state

        self.connect_robot()
        self.init_robot()
    
    def init_robot(self):
        """
        Initializes the robot by clearing any errors and enabling the robot. (Thread-safe)
        """
        with self.dashboard_lock:
            self._dashboard.ClearError()
            time.sleep(0.5)
            self._dashboard.EnableRobot()

    #def connect(self):
    #    res = self.LS.ConnectSimpleW(11, self.port, 115200, True)
    #    if res == 0:
    #        print("Connected")
    #    self.LS.LoadConfigW(self.dllconfigpath)
    #    self.connected = True
        
    def connect_robot(self):
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
            self._dashboard = DobotApiDashboard(
                self.robot_ip, self.dashboard_port, False
            )
            self._move = DobotApiMove(self.robot_ip, self.move_port, False)
            self.log_robot("Connection successful")
        except Exception as e:
            self.log_robot("Connection failure")
            raise e   

    #def disconnect(self):
    #    res = self.LS.Disconnect()
    #    if res == 0:
    #        print("Disconnected")
    #
    #    self.connected = False
        
    def close_robot(self):
        """
        Closes the robot connection. (Thread-safe)
        """
        with self.dashboard_lock:
            self._dashboard.DisableRobot() 
            time.sleep(0.5)
            self._dashboard.close()
        self._move.close()

    #def getPos(self):
    #    ans = self.LS.GetPos(0,0,0,0)
    #    return ans [1:-1]

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

    #def moveRelFar(self,dx,dy,dz):
    #    if dz > 0: #moving down -> z last
    #        self.moveRelXY(dx,dy)
    #        self.moveRelZ(dz)
    #    if dz <= 0: # moving up -> z first
    #        self.moveRelZ(dz)
    #        self.moveRelXY(dx,dy)

    #def moveRelZ(self,dz,wait=True):
    #    self.LS.MoveRel(0,0,dz,0,wait)
            
    #def moveRelXY(self,dx,dy,wait=True):
    #    self.LS.MoveRel(dx,dy,0,0,wait)

    #def moveAbsXY(self,x,y,wait=True):
    #    xp,yp,zp = self.getPos()
    #    self.LS.MoveAbs(x,y,zp,0,wait)

    #code from lang robot
    def isMoving(self,):
        pass
    
    def move_linear_relative(self, movement):
        """
        Moves the robot relative to the current joint positions linearly.

        Args:
            movement (tuple): A tuple of relative joint movements.
        """
        self._move.RelMovL(*movement)
        self._move.Sync()

    #def moveAbsZ(self, z, wait=True):
        #raise do not use this function 
    #    xp,yp,zp = self.getPos()
    #    self.LS.MoveAbs(xp,yp,z,0,wait)


    #def moveAbsFar(self, dx, dy, dz): 
    #    if dz > 0: #moving down -> z last
    #        self.moveAbsXY(dx,dy)
    #        self.moveAbsZ2(dz)
    #    if dz <= 0: # moving up -> z first
    #        self.moveAbsZ2(dz)
    #        self.moveAbsXY(dx,dy)

    #def setMaxVel(self,xvel,yvel,zvel):
    #    self.LS.SetVel(xvel,yvel,zvel,0)

    def set_linear_speed(self, speed):
        """
        Sets the linear speed of the robot. (Thread-safe)

        Args:
            speed (int): The desired linear speed.
        """
        self.log_robot(f"Setting linear speed to {speed}")
        with self.dashboard_lock:
            self._dashboard.SpeedL(int(speed))

    #def moveAbsZ2(self,z,wait=True):
    #    self.moveRelZ(z-self.getPos()[2],wait)

    #code from lang robot
    def stopMove(self):
        self.LS.StopAxes()

    def robot_is_alive(self):
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
        self.close_robot()
        time.sleep(0.5)
        self.connect_robot()
        self.init_robot()

    def log_robot(self, msg: str):
        """
        Logs a message with the robot identifier.

        Args:
            msg (str): The message to be logged.
        """
        self.print_function(msg, f"Robot {self.identifier}")

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
        error_codes_str = s[s.find("[") : s.rfind("]") + 1]
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
        return np.fromstring(s[s.find("{") + 1 : s.find("}")], sep=",")[
            : self.number_of_joints
        ]

    def extract_angles(self, s):
        return np.fromstring(s[s.find("{") + 1 : s.find("}")], sep=",")[
            : self.number_of_joints
        ]

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

    def replay(self, memory):
        """
        Replays a sequence of robot movements stored in the memory.

        Args:
            memory (list): A list of memory entries representing the robot movements.
        """
        self.log_robot("Replaying")
        for i, entry in enumerate(memory):
            if entry.type == MemoryType.ABSOLUTE:
                if entry.motion_type == MotionType.LINEAR:
                    func = self.move_linear_absolute
                elif entry.motion_type == MotionType.JOINT:
                    func = self.move_joint_absolute
            elif entry.type == MemoryType.RELATIVE:
                if entry.motion_type == MotionType.LINEAR:
                    func = self.move_linear_relative
                elif entry.motion_type == MotionType.JOINT:
                    func = self.move_joint_relative
            elif entry.type == MemoryType.END_EFFECTOR:
                for index, value in entry.value:
                    self.set_digital_output(index, value)
                    time.sleep(0.1)
                continue

            result = self.nonblocking_move(func, entry.value)
            if not result:
                self.log_robot(
                    f"Error replaying from {self.pose if entry.motion_type == MemoryType.ABSOLUTE else self.angles} "
                )
                self.log_robot(f"Error replaying to {entry.value}")
                for j in range(i, len(memory)):
                    memory[j].valid = False
                break
            self._move.Sync()
        self.log_robot("Done Replaying")