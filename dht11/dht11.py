#!/usr/bin/python

import RPi.GPIO as GPIO
import os
import sys
import rrdtool
import time
from time import gmtime, strftime, sleep
import urllib2
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from tendo import singleton
import logging
import logging.handlers
import SimpleHTTPServer
import SocketServer
from socket import error as socket_error
import thread
import atexit
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

#Ensures only one instance of this script is running at a time
me = singleton.SingleInstance() 


nodeName = os.getenv('NODE_NAME')
rrdPath = "/home/pi/data/"
rrdName = nodeName + ".rrd"
graphName = nodeName + ".png"
detailedGraphName = nodeName + "_detailed.png"

httpPort = os.getenv('HTTP_PORT')
awsS3Key = "images/" + nodeName +".png"
awsS3KeyDetailed = "images/" + nodeName + "_detailed.png"
awsAccessKey = os.getenv('AWS_ACCESS_KEY')
awsSecretKey = os.getenv('AWS_SECRETE_KEY')
awsS3Bucket = os.getenv('AWS_BUCKET')

rrdFile = rrdPath + rrdName
graphPath = rrdPath + graphName
detailedGraphPath = rrdPath + detailedGraphName

data_sources = ['DS:temperature:GAUGE:600:U:U',
                'DS:humidity:GAUGE:600:U:U',
                'DS:pressure:GAUGE:600:U:U' ]


LOG_FILENAME = '/home/pi/data/' + nodeName  + '.log'

# Set up a specific logger with our desired output level
logger = logging.getLogger(nodeName)
logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=2)
logger.addHandler(handler)



def bin2dec(string_num):
    return str(int(string_num, 2))

def readSensor():
    maxRetries = 10
    gpio_pin = 25

    retryNum = 0
    while(retryNum < maxRetries):
        if retryNum > 0:
            sleep(1.1)

        retryNum = retryNum + 1
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(gpio_pin,GPIO.OUT)
        GPIO.output(gpio_pin,GPIO.HIGH)
        time.sleep(0.025)
        GPIO.output(gpio_pin,GPIO.LOW)
        time.sleep(0.02)

        GPIO.setup(gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        data = []
        for i in range(0,500):
            data.append(GPIO.input(gpio_pin))

        bit_count = 0
        tmp = 0
        count = 0
        HumidityBit = ""
        TemperatureBit = ""
        crc = ""

        try:
            while data[count] == 1:
                tmp = 1
                count = count + 1

            for i in range(0, 32):
                bit_count = 0

                while data[count] == 0:
                    tmp = 1
                    count = count + 1

                while data[count] == 1:
                    bit_count = bit_count + 1
                    count = count + 1

                if bit_count > 3:
                    if i>=0 and i<8:
                        HumidityBit = HumidityBit + "1"
                    if i>=16 and i<24:
                        TemperatureBit = TemperatureBit + "1"
                else:
                    if i>=0 and i<8:
                        HumidityBit = HumidityBit + "0"
                    if i>=16 and i<24:
                        TemperatureBit = TemperatureBit + "0"

        except:
            logger.info("DHT11 ERR_RANGE")
            continue

        try:
            for i in range(0, 8):
                bit_count = 0

                while data[count] == 0:
                    tmp = 1
                    count = count + 1

                while data[count] == 1:
                    bit_count = bit_count + 1
                    count = count + 1

                if bit_count > 3:
                    crc = crc + "1"
                else:
                    crc = crc + "0"
        except:
            logger.info("DHT11 ERR_RANGE")
            continue

        Humidity = bin2dec(HumidityBit)
        Temperature = bin2dec(TemperatureBit)

        if int(Humidity) + int(Temperature) - int(bin2dec(crc)) == 0:
            return int(Temperature), int(Humidity)
        else:
            logger.info("DHT11 ERROR_CRC")
            continue
    return -1, -1


def getOrCreateRrd():
    if(not os.path.isfile(rrdFile)):
        logger.info("Creating " + rrdFile)
        rrdtool.create( rrdFile,
                '--start', '-10',
                '--step', '10',
                data_sources,
                'RRA:AVERAGE:0.5:1:320000',
                'RRA:MIN:0.5:360:40000',
                'RRA:MAX:0.5:360:40000',
                'RRA:AVERAGE:0.5:360:40000')

def updateGraph(lastUpdated, awsS3Bucket, awsS3Key, graphPath):
    global temperature, pressure, humidity
    if(time.time() - lastUpdated > 300):
        logger.info("Updating Graph...")
        rrdtool.graph(graphPath,
                '--imgformat', 'PNG',
                '--width', '500',
                '--height', '200',
                '--start', "-10492000",
                '--end', "-1",
                '--right-axis', '1:950',
                '--title', nodeName + ' 120 Day - Temperature, Humidity, Pressure',
                '--watermark', 'Generated at ' + strftime("%m-%d-%Y %H:%M:%S", time.localtime()),
                "DEF:temperature_raw="+rrdFile+":temperature:AVERAGE",
                "DEF:pressure="+rrdFile+":pressure:AVERAGE",
                "DEF:humidity="+rrdFile+":humidity:AVERAGE",
                "CDEF:scaled_pressure=pressure,950,-",
                "COMMENT:Last\: Temperature - " + str(temperature) + ", Pressure - " + str(pressure) + ", Humidity - " + str(humidity)  + "%",
                "LINE1:humidity#00FF00:Humidity       ",
                'GPRINT:humidity:LAST:Last\:%5.2lf %s',
                "GPRINT:humidity:AVERAGE:Avg\:%5.2lf %s",
                "GPRINT:humidity:MAX:Max\:%5.2lf %s",
                "GPRINT:humidity:MIN:Min\:%5.2lf %s\\n",
                "LINE2:scaled_pressure#0000FF:Pressure hpa   ",
                "GPRINT:pressure:LAST:Last\:%5.3lf %s",
                "GPRINT:pressure:AVERAGE:Avg\:%5.3lf %s",
                "GPRINT:pressure:MAX:Max\:%5.3lf %s",
                "GPRINT:pressure:MIN:Min\:%5.3lf %s\\n",
                "LINE1:temperature_raw#FF0000:Temperature    ",
                "GPRINT:temperature_raw:LAST:Last\:%5.2lf %s",
                "GPRINT:temperature_raw:AVERAGE:Avg\:%5.2lf %s",
                "GPRINT:temperature_raw:MAX:Max\:%5.2lf %s",
                "GPRINT:temperature_raw:MIN:Min\:%5.2lf %s\\n",
                '--right-axis-format','%1.1lf')
        s3Upload(awsS3Bucket, awsS3Key, graphPath)
        return time.time()
    return lastUpdated

def updateDetailedGraph(lastUpdated, awsS3Bucket, awsS3Key, graphPath):
    if(time.time() - lastUpdated > 300):
        logger.info("Updating Graph...")
        rrdtool.graph(graphPath,
                '--imgformat', 'PNG',
                '--width', '500',
                '--height', '200',
                '--start', "-172800",
                '--end', "-1",
                '--right-axis', '1:950',
                '--title', nodeName + ' - 48 Hour Temperature, Humidity, Pressure',
                '--watermark', 'Generated at ' + strftime("%m-%d-%Y %H:%M:%S", time.localtime()),
                "DEF:temperature_raw="+rrdFile+":temperature:AVERAGE",
                "DEF:pressure="+rrdFile+":pressure:AVERAGE",
                "DEF:humidity="+rrdFile+":humidity:AVERAGE",
                "CDEF:scaled_pressure=pressure,950,-",
                "COMMENT:Last\: Temperature - " + str(temperature) + ", Pressure - " + str(pressure) + ", Humidity - " + str(humidity)  + "%",
                "LINE1:humidity#00FF00:Humidity       ",
                'GPRINT:humidity:LAST:Last\:%5.2lf %s',
                "GPRINT:humidity:AVERAGE:Avg\:%5.2lf %s",
                "GPRINT:humidity:MAX:Max\:%5.2lf %s",
                "GPRINT:humidity:MIN:Min\:%5.2lf %s\\n",
                "LINE2:scaled_pressure#0000FF:Pressure hpa   ",
                "GPRINT:pressure:LAST:Last\:%5.3lf %s",
                "GPRINT:pressure:AVERAGE:Avg\:%5.3lf %s",
                "GPRINT:pressure:MAX:Max\:%5.3lf %s",
                "GPRINT:pressure:MIN:Min\:%5.3lf %s\\n",
                "LINE1:temperature_raw#FF0000:Temperature    ",
                "GPRINT:temperature_raw:LAST:Last\:%5.2lf %s",
                "GPRINT:temperature_raw:AVERAGE:Avg\:%5.2lf %s",
                "GPRINT:temperature_raw:MAX:Max\:%5.2lf %s",
                "GPRINT:temperature_raw:MIN:Min\:%5.2lf %s\\n",
                '--right-axis-format','%1.1lf')
        s3Upload(awsS3Bucket, awsS3Key, graphPath)
        return time.time()
    return lastUpdated

def s3Upload(targetBucket, targetKey, fromPath ):
    global awsAccessKey, awsSecretKey
    if awsAccessKey is not None:
        logger.info("Uploading " + fromPath + " to " + "s3:" + targetBucket + "/" + targetKey)
        conn = S3Connection(awsAccessKey,awsSecretKey)
        bucket = conn.get_bucket(targetBucket)
        k = Key(bucket)
        k.key = targetKey
        k.set_contents_from_filename(fromPath)
    else:
        logger.info("AWS integration disabled since awsAccessKey is None")


class GraphHttpHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(),format%args))
    def do_HEAD(s):
        if(s.path == '/map'):
            s.send_response(200)
            s.send_header("Content-type", "image/jpeg")
            s.end_headers()
        else:
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()

    def do_GET(s):
        global graphPath, detailedGraphPath, nodeName
        if( s.path == '/rrd-graph-history' ):
            s.send_response(200)
            s.send_header("Content-type", "image/jpeg")
            s.end_headers()
            f = open(graphPath)
            s.wfile.write(f.read())
            f.close()
        elif( s.path == '/rrd-graph-recent' ):
            s.send_response(200)
            s.send_header("Content-type", "image/jpeg")
            s.end_headers()
            f = open(detailedGraphPath)
            s.wfile.write(f.read())
            f.close()
        else:
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()

            s.wfile.write("<html><head><title>{}</title></head><body>".format(nodeName))
            s.wfile.write("<br><img src='/rrd-graph-history'</img>")
            s.wfile.write("<br>&nbsp;<br><img src='/rrd-graph-recent'</img>")
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

temperature = 0
pressure = 0
humidity = 0

def main():
    global temperature, pressure, humidity

    lastUpdated = 0
    detailedLastUpdated = 0
    while(1):
        getOrCreateRrd()
        pressure = 0    #not supported
        temperature,humidity = readSensor()
        temperature = (temperature * 9/5) + 32
        logger.info("Temperature : {} F, Pressure: {} hPa, Humidity: {}%".format(temperature,pressure,humidity))
        if(temperature != -1 or humidity != -1):
            ret = rrdtool.update(rrdFile, '%s:%s:%s:%s' %(time.time(),temperature, humidity, pressure));
            logger.info("Updated RRD " + str(ret))

            lastUpdated = updateGraph(lastUpdated, awsS3Bucket, awsS3Key, graphPath)
            detailedLastUpdated = updateDetailedGraph(detailedLastUpdated, awsS3Bucket, awsS3KeyDetailed, detailedGraphPath)
        time.sleep(10)

if __name__=="__main__":
    try:
        thread.start_new_thread( web_ui, ())
        main()
    except KeyboardInterrupt:
        shutdown()
   
