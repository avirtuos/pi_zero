#!/usr/bin/python

from picamera.array import PiRGBArray
from picamera import PiCamera
from tendo import singleton
import urllib2
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import cv2
import argparse
import warnings
import datetime
import imutils
import json
import time
import uuid
import os
import sys

#Ensures only one instance of this script is running at a time
me = singleton.SingleInstance()	

class TempImage:
	def __init__(self, basePath="/home/pi/data/", ext=".jpg"):
		# construct the file path
		self.path = "{base_path}/{rand}{ext}".format(base_path=basePath,
			rand=str(uuid.uuid4()), ext=ext)

	def cleanup(self):
		# remove the file
		os.remove(self.path)

	def printPath(self):
		print "PATH: " + self.path;

nodeName = os.environ['NODE_NAME']
awsS3Key = "images/surveillance_" + nodeName +".jpg"
awsAccessKey = os.environ['AWS_ACCESS_KEY']
awsSecretKey = os.environ['AWS_SECRETE_KEY']
awsS3Bucket = os.environ['AWS_BUCKET']

def s3Upload(fromPath ):
	global awsS3Key, awsS3Bucket, awsAccessKey, awsSecretKey
	print "Uploading " + fromPath + " to " + "s3:" + awsS3Bucket + "/" + awsS3Key
	conn = S3Connection(awsAccessKey,awsSecretKey)
	bucket = conn.get_bucket(awsS3Bucket)
	k = Key(bucket)
	k.key = awsS3Key
	k.set_contents_from_filename(fromPath)

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
args = vars(ap.parse_args())

imageCapture = 0

# filter warnings, load the configuration and initialize the Dropbox
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = conf["resolution"]
camera.framerate = conf["fps"]
#camera.rotation = '180'
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))

# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print "[INFO] warming up..."
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0


camera.capture('/home/pi/data/image.jpg')

# capture frames from the camera
for f in camera.capture_continuous(rawCapture, format="bgr"):
	print "[INFO] Checking frame... imageCapture: " + str(imageCapture)
		
	# grab the raw NumPy array representing the image and initialize
	# the timestamp and occupied/unoccupied text
	frame = f.array
	timestamp = datetime.datetime.now()
	text = "Unoccupied"

	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=1280)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)

	# if the average frame is None, initialize it
	if avg is None or imageCapture > 60:
		imageCapture = 0
		print "[INFO] starting background model..."
		avg = gray.copy().astype("float")
		print "[INFO] completed background model..."
		rawCapture.truncate(0)
		continue

	# accumulate the weighted average between the current frame and
	# previous frames, then compute the difference between the current
	# frame and running average
	cv2.accumulateWeighted(gray, avg, 0.5)
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

	# threshold the delta image, dilate the thresholded image to fill
	# in holes, then find contours on thresholded image
	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
		cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=2)
	(cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)

	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < conf["min_area"]:
			continue

		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Occupied"
		print "[INFO] Occupied..."

	# draw the text and timestamp on the frame
	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 4)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 4)

	# check to see if the room is occupied
	if text == "Occupied":
		imageCapture += 1
		print "[Occupied!] {}".format(ts)
		# check to see if enough time has passed between uploads
		if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
			# increment the motion counter
			motionCounter += 1

			# check to see if the number of frames with consistent motion is
			# high enough
			if motionCounter >= conf["min_motion_frames"]:
				
				t2 = TempImage()
				cv2.imwrite(t2.path, frame)
				s3Upload(t2.path)
				print "[INFO] Occupied " + t2.path


				# update the last uploaded timestamp and reset the motion
				# counter
				lastUploaded = timestamp
				motionCounter = 0

	# otherwise, the room is not occupied
	else:
		if motionCounter > 0:
			motionCounter -= 1
		else:
			motionCounter = 0

	# check to see if the frames should be displayed to screen
	if conf["show_video"]:
		# display the security feed
		cv2.imshow("Security Feed", frame)
		key = cv2.waitKey(1) & 0xFF

		# if the `q` key is pressed, break from the lop
		if key == ord("q"):
			break

	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)