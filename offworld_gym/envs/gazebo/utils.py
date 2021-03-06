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

import numpy as np
import cv2
import rospy
from std_srvs.srv import Empty as Empty_srv
from cv_bridge import CvBridge, CvBridgeError
from gazebo_msgs.srv import GetModelState, SetModelState
from gazebo_msgs.msg import ModelState

class GazeboUtils:
    """Gazebo utility functions used by the OffWorld Gym environments
    """

    unpause = rospy.ServiceProxy('/gazebo/unpause_physics', Empty_srv)
    pause = rospy.ServiceProxy('/gazebo/pause_physics', Empty_srv)

    @staticmethod
    def unpause_physics(): 
        """Unpause physics of the Gazebo simulator
        """       
        rospy.wait_for_service('/gazebo/unpause_physics')
        try:
            GazeboUtils.unpause()
        except rospy.ServiceException:
            rospy.logerr("/gazebo/pause_physics service call failed")

    @staticmethod
    def pause_physics():
        """Pause physics of the Gazebo simulator
        """
        rospy.wait_for_service('/gazebo/pause_physics')
        try:
            GazeboUtils.pause()
        except rospy.ServiceException:
            rospy.logerr("/gazebo/unpause_physics service call failed")
    
    @staticmethod
    def move_to_position(model_state):
        """Set a model's state
        Args:
            model_state: A ModelState object with the model's state details
        Raises:
             Exception: Exception occured during the /gazebo/set_model_state 
             service call
        """
        try:
            assert isinstance(model_state, ModelState)
            rospy.wait_for_service('/gazebo/set_model_state')
            set_model_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)
            set_model_state(model_state)
        except rospy.ServiceException as e:
            rospy.logerr('The robot cannot be reset.')
            raise e

class ImageUtils(object):
    """Image utility functions used by the OffWorld Gym environments
    """
    IMG_H = 240
    IMG_W = 320
    IMG_C = 3

    @staticmethod
    def process_img_msg(img_msg, resized_width=IMG_W, resized_height=IMG_H, max_value_for_clip_and_normalize=None):
        """Converts ROS image to cv2, then to numpy
        """
        img = CvBridge().imgmsg_to_cv2(img_msg, "bgr8")
        img = np.asarray(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (resized_width, resized_height))

        img = np.reshape(img, (1, img.shape[0], img.shape[1], img.shape[2]))

        if max_value_for_clip_and_normalize is not None:
            img = np.clip(img, a_min=0.0, a_max=max_value_for_clip_and_normalize)
            img = img / max_value_for_clip_and_normalize

        return img 
    
    @staticmethod
    def process_depth_msg(depth_msg, resized_width=IMG_W, resized_height=IMG_H, max_value_for_clip_and_normalize=None):
        """Converts a depth image into numpy float32 array
        """
        cv_image = CvBridge().imgmsg_to_cv2(depth_msg, "32FC1")
        img = np.asarray(cv_image, dtype=np.float32)
        img = np.nan_to_num(img)
        img = cv2.resize(img, (resized_width, resized_height))

        img = np.reshape(img, (1, img.shape[0], img.shape[1], 1))

        if max_value_for_clip_and_normalize is not None:
            img = np.clip(img, a_min=0.0, a_max=max_value_for_clip_and_normalize)
            img = img / max_value_for_clip_and_normalize

        return img

