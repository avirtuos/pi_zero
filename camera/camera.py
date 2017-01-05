#!/usr/bin/python
import os
import sys
import time
from time import gmtime, strftime, sleep
import urllib2
from tendo import singleton
import logging
import logging.handlers
import SimpleHTTPServer
import SocketServer
from socket import error as socket_error
import thread
import atexit
import picamera
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

#Ensures only one instance of this script is running at a time
me = singleton.SingleInstance() 

httpPort="8000"
LOG_FILENAME = '/home/pi/data/pi_camera.log'
CAMERA_IMAGE_LOC = '/home/pi/data/pi_camera_image.jpg'

# Set up a specific logger with our desired output level
logger = logging.getLogger('PiCam')
logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=2)
logger.addHandler(handler)



class GraphHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(),format%args))
    def do_HEAD(s):
        if(s.path == '/camera'):
            s.send_response(200)
            s.send_header("Content-type", "image/jpeg")
            s.end_headers()
        else:
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()

    def do_GET(s):
        global CAMERA_IMAGE_LOC
        if( s.path == '/camera' ):
            s.send_response(200)
            s.send_header("Content-type", "image/jpeg")
            s.end_headers()
            f = open(CAMERA_IMAGE_LOC)
            s.wfile.write(f.read())
            f.close()
        else:
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
            s.wfile.write("<html><head><title>Pi Camera</title></head><body>")
            s.wfile.write("<br><img src='/camera'</img>")
            s.wfile.write("</body></html>")

httpd = None
def web_ui():
    global httpd, httpPort
    if httpPort is not None:
        Handler = GraphHttpHandler
        httpd = None

        while httpd == None:
            try:
                httpd = SocketServer.TCPServer(("", int(httpPort)), Handler)
                logger.info("Started web server on port {}".format(httpPort))
            except socket_error as err:
                httpd = None
                logger.info("Error {0} starting http servier, retrying after sleeping 4 seconds.".format(err))
                sleep(4)

        atexit.register(shutdown)
        #rospy.loginfo('HTTP Server started on port: %d',  PORT)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            server.socket.close()

def shutdown():
    global httpd, port
    if httpPort is not None:
        logger.info("Shutting down...")
        httpd.shutdown()
        httpd.server_close()



def main():
	camera = picamera.PiCamera()
	try:
		while 1:
			logger.info("Updating camera image...")
			camera.resolution = '1024x768' #'3280 x 2464'
			#camera.rotation = '180'
			camera.meter_mode = 'average'
			camera.capture(CAMERA_IMAGE_LOC)
			sleep(5)
	finally:
		camera.close()

if __name__=="__main__":
    try:
        thread.start_new_thread( web_ui, ())
        main()
    except KeyboardInterrupt:
        shutdown()

