#!/usr/bin/python
import os
import sys
import rrdtool
import time
from time import gmtime, strftime
import urllib2
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from bme280 import Bme280Sensor
from tendo import singleton
import logging
import logging.handlers

#Ensures only one instance of this script is running at a time
me = singleton.SingleInstance()	


nodeName = "pi-139 bme"
rrdPath = "/home/pi/data/"
rrdName = "bme280.rrd"
graphName = "bme280.png"

awsS3Key = "images/pi_139_bme280.png"
awsAccessKey = os.environ['AWS_ACCESS_KEY']
awsSecretKey = os.environ['AWS_SECRETE_KEY']
awsS3Bucket = os.environ['AWS_BUCKET']
awsS3Key = "images/pi_139_bme280.png"

rrdFile = rrdPath + rrdName
graphPath = rrdPath + graphName

data_sources = ['DS:temperature:GAUGE:600:U:U',
                'DS:humidity:GAUGE:600:U:U',
                'DS:pressure:GAUGE:600:U:U' ]


LOG_FILENAME = '/home/pi/data/pi_collectd.log'

# Set up a specific logger with our desired output level
logger = logging.getLogger('PiCollectd')
logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=2)
logger.addHandler(handler)

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
	if(time.time() - lastUpdated > 300):
		logger.info("Updating Graph...")
		rrdtool.graph(graphPath,
	            '--imgformat', 'PNG',
	            '--width', '500',
	            '--height', '200',
	            '--start', "-86400",
	            '--end', "-1",
	            '--right-axis', '1:950',
	            '--title', 'pi-0-139 BME280 - Temperature, Humidity, Pressure',
				'--watermark', 'Generated at ' + strftime("%m-%d-%Y %H:%M:%S", time.localtime()),
	            "DEF:temperature_raw=/home/pi/data/bme280.rrd:temperature:AVERAGE",
				"DEF:temperature_avg=/home/pi/data/bme280.rrd:temperature:AVERAGE:step=360",
				"DEF:temperature_min=/home/pi/data/bme280.rrd:temperature:MIN",
				"DEF:temperature_max=/home/pi/data/bme280.rrd:temperature:MAX",
				"DEF:pressure=/home/pi/data/bme280.rrd:pressure:AVERAGE",
				"DEF:humidity=/home/pi/data/bme280.rrd:humidity:AVERAGE",
				"CDEF:scaled_pressure=pressure,950,-",
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
				"LINE1:temperature_min#e040fb:Temperature Min",
				"GPRINT:temperature_min:LAST:Last\:%5.2lf %s",
				"GPRINT:temperature_min:AVERAGE:Avg\:%5.2lf %s",
				"GPRINT:temperature_min:MAX:Max\:%5.2lf %s",
				"GPRINT:temperature_min:MIN:Min\:%5.2lf %s\\n",
				"LINE1:temperature_max#e040fb:Temperature Max",
				"GPRINT:temperature_max:LAST:Last\:%5.2lf %s",
				"GPRINT:temperature_max:AVERAGE:Avg\:%5.2lf %s",
				"GPRINT:temperature_max:MAX:Max\:%5.2lf %s",
				"GPRINT:temperature_max:MIN:Min\:%5.2lf %s\\n",
				"LINE2:temperature_avg#FF4081:Temperature Avg",
				"GPRINT:temperature_avg:LAST:Last\:%5.2lf %s",
				"GPRINT:temperature_avg:AVERAGE:Avg\:%5.2lf %s",
				"GPRINT:temperature_avg:MAX:Max\:%5.2lf %s",
				"GPRINT:temperature_avg:MIN:Min\:%5.2lf %s\\n",
	            '--right-axis-format','%1.1lf')
		s3Upload(awsS3Bucket, awsS3Key, graphPath)
		return time.time()
	return lastUpdated

def s3Upload(targetBucket, targetKey, fromPath ):
	global awsAccessKey, awsSecretKey
	logger.info("Uploading " + fromPath + " to " + "s3:" + targetBucket + "/" + targetKey)
	conn = S3Connection(awsAccessKey,awsSecretKey)
	bucket = conn.get_bucket(targetBucket)
	k = Key(bucket)
	k.key = targetKey
	k.set_contents_from_filename(fromPath)


def main():
	sensor = Bme280Sensor()

	warmUp = 0
	while warmUp < 15:
		logger.info("Warm Up: " + str(warmUp))
		warmUp = warmUp + 1
		(chip_id, chip_version) = sensor.readBME280ID()
		logger.info("Chip ID     :" + str(chip_id))
		logger.info("Version     :" + str(chip_version))
		temperature,pressure,humidity = sensor.readBME280All()
		temperature = (temperature * 9/5) + 32
		logger.info("Temperature : " + str(temperature) + "C")
		logger.info("Pressure : " + str(pressure) + "hPa")
		logger.info("Humidity : " + str(humidity) + "%")
		time.sleep(1)

	lastUpdated = 0
	while(1):
		getOrCreateRrd()
		temperature,pressure,humidity = sensor.readBME280All()
		temperature = (temperature * 9/5) + 32
		logger.info("Temperature : " + str(temperature) + "C")
		logger.info("Pressure : " + str(pressure) + "hPa")
		logger.info("Humidity : " + str(humidity) + "%")

		ret = rrdtool.update(rrdFile, '%s:%s:%s:%s' %(time.time(),temperature, humidity, pressure));
		logger.info("Updated RRD " + ret)

		lastUpdated = updateGraph(lastUpdated, awsS3Bucket, awsS3Key, graphPath)

		time.sleep(10)

if __name__=="__main__":
   main()