from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime

import cv2
import time
import ctypes
import _ctypes
import sys
import numpy as np

if sys.hexversion >= 0x03000000:
	import _thread as thread
else:
	import thread

class AcquisitionKinect():
	#Create a constructor to initialize different types of array and frame objects
	def __init__(self, resolution_mode=1.0):
		self.resolution_mode = resolution_mode

		self._done = False

		# Kinect runtime object, we want only color and body frames
		self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body | PyKinectV2.FrameSourceTypes_Depth)

		# here we will store skeleton data
		self._bodies = None
		self.body_tracked = False
		self.joint_points = np.array([])
		self.joint_points3D = np.array([])
		self.joint_points_RGB = np.array([])
		self.joint_state = np.array([])

		self._frameRGB = None
		self._frameDepth = None
		self._frameDepthQuantized = None
		self._frameSkeleton = None
		self.frameNum = 0

	def get_frame(self, frame):
		self.acquireFrame()
		frame.ts = int(round(time.time() * 1000))

		self.frameNum += 1

		frame.frameRGB = self._frameRGB
		frame.frameDepth = self._frameDepth
		frame.frameDepthQuantized = self._frameDepthQuantized
		frame.frameSkeleton = self._frameSkeleton

	#Get a color frame object
	def get_color_frame(self):
	   self._frameRGB = self._kinect.get_last_color_frame()
	   self._frameRGB = self._frameRGB.reshape((1080, 1920,-1)).astype(np.uint8)
	   self._frameRGB = cv2.resize(self._frameRGB, (0,0), fx=1/self.resolution_mode, fy=1/self.resolution_mode)

	#Get depth from Frame
	def get_depth_frame(self):
		self._frameDepth = self._kinect.get_last_depth_frame()
		self._frameDepth = self._frameDepth.reshape(((424, 512))).astype(np.uint16)
		self._frameDepthQuantized = ((self._frameDepth.astype(np.int32)-500)/8.0).astype(np.uint8)

	#Get Camera Coordinates from Joints
	def get_eye_camera_space_coord(self):
		self._bodies = self._kinect.get_last_body_frame()
		max_body_count = self._kinect.max_body_count
		for i in range(0, max_body_count):
			body = self._bodies.bodies[i]
			if body.is_tracked:
				#self.joint_points3D = np.append(self.joint_points3D,np.array([body.joints2[2][1]])) 
				self.joint_points3D = np.array([body.joints2[2][1][0],body.joints2[2][1][1],body.joints2[2][1][2]])

	# Transform Depth points of interest into Camera space points 
	def acquireCameraSpace(self, depthpoints, depths):
		n = len(depthpoints)
		points_cam = np.array([])
		assert n == len(depths)
		for i in range(n):
			depthpoint = PyKinectV2._DepthSpacePoint()
			depthpoint.x = depthpoints[i][0]
			depthpoint.y = depthpoints[i][1]
			space_point = self._kinect.depth_to_camera(depthpoint, depths[i])
			points_cam = np.append(points_cam, np.array([space_point.x, space_point.y, space_point.z]))
		return points_cam

	#Acquire the type of frame required
	def acquireFrame(self):
		if self._kinect.has_new_color_frame():
			self.get_color_frame()
		if self._kinect.has_new_depth_frame():
			self.get_depth_frame()
	def close(self):
		self._kinect.close()
		self._frameDepth = None
		self._frameRGB = None
		self._frameSkeleton = None
