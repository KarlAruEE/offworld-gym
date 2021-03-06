#!/usr/bin/env python

# Copyright 2019 OffWorld Inc.
# Doing business as Off-World AI, Inc. in California.
# All rights reserved.
#
# Licensed under GNU General Public License v3.0 (the "License")
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at https://www.gnu.org/licenses/gpl-3.0.en.html
#
# Unless required by applicable law, any source code or other materials
# distributed under the License is distributed on an "AS IS" basis,
# without warranties or conditions of any kind, express or implied.

from offworld_gym import version

__version__     = version.__version__

#std
import os
import sys
import time
import subprocess
import signal
import psutil
import threading
from abc import abstractmethod
from abc import ABCMeta

#gym
from offworld_gym import logger
import gym
from gym import error, spaces, utils
from gym.utils import seeding
from offworld_gym.envs.common.exception.gym_exception import GymException

#ros
gazebo_gym_python_dependencies: str = os.environ.get("GAZEBO_GYM_PYTHON_DEPENDENCIES", None)
if gazebo_gym_python_dependencies is not None:
    for dependency in gazebo_gym_python_dependencies.split(":"):
        sys.path.append(dependency)

import rospy
import rospkg


class GazeboGymEnv(gym.Env, metaclass=ABCMeta):
    """Base class for Gazebo based Gym environments

    Attributes:
        package_name: String containing the ROS package name
        launch_file: String containing the name of the environment's launch file.
        node_name: String with a ROS node name for the environment's node
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, package_name, launch_file, node_name='gym_offworld_env'):

        assert package_name is not None and package_name != '', "Must provide a valid package name."
        assert launch_file is not None and launch_file != '', "Must provide a valid launch file name."
        
        self.package_name = package_name
        self.launch_file = launch_file
        self.node_name = node_name

        try:
            self.launch_node()
        except:
            import traceback
            traceback.print_exc()

    def launch_node(self):
        """Launches the gazebo world 

        Launches a ROS node containing a gazebo world, spawns a robot in the world
        """
        try:
            rospack = rospkg.RosPack()
            if rospack.get_path(self.package_name) is None:
                raise GymException("The ROS package does not exist.")

            ros_env = os.environ.copy()
            if ros_env.get("ROSLAUNCH_PYTHONPATH_OVERRIDE", None) is not None:
                ros_env["PYTHONPATH"] = ros_env["ROSLAUNCH_PYTHONPATH_OVERRIDE"]

            self.roslaunch_process = subprocess.Popen(['roslaunch', os.path.join(rospack.get_path(self.package_name), "launch", self.launch_file)], env=ros_env)
            self.roslaunch_wait_thread = threading.Thread(target=self._process_waiter, args=(1,))
            self.roslaunch_wait_thread.start()
        except OSError:
            print("Ros node could not be started.")
            import traceback
            traceback.print_exc() 

        rospy.loginfo("The environment has been started.")
        rospy.init_node(self.node_name, anonymous=True)
        rospy.on_shutdown(self.close)

    def _process_waiter(self, popen):
        try: 
            self.roslaunch_process.wait()
            logger.info("Roslaunch has finished.")
        except: 
            logger.error("An error occured while waiting for roslaunch to finish.")

    @abstractmethod
    def step(self, action):
        """Abstract step method to be implemented in a child class
        """
        raise NotImplementedError
    
    @abstractmethod
    def reset(self):
        """Abstract reset method to be implemented in a child class
        """
        raise NotImplementedError
    
    @abstractmethod
    def render(self, mode='human'):
        """Abstract render method to be implemented in a child class
        """
        raise NotImplementedError
    
    def close(self):
        """Closes environment and all processes created for the environment
        """
        rospy.loginfo("Closing the environment and all processes. ")
        try:
            launch_process = psutil.Process(self.roslaunch_process.pid)
            launch_children = launch_process.children(recursive=True)
            for process in launch_children:
                process.send_signal(signal.SIGTERM)
        except:
            import traceback
            traceback.print_exc()
        
        #force any lingering processes to shutdown
        os.system("killall -9 -u `whoami` gzclient")
        os.system("killall -9 -u `whoami` gzserver")
        os.system("killall -9 -u `whoami` rosmaster")
        os.system("killall -9 -u `whoami` roscore")


