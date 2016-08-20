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

nodeName = "pi-139 bme"
rrdPath = "/home/pi/data/"
rrdName = "bme280.rrd"
graphName = "bme280.png"
awsAccessKey = "ACCESS_KEY_HERE"
awsSecretKey = "SECRET_KEY_HERE"
awsS3Bucket = "BUCKET_HERE"
awsS3Key = "images/pi_139_bme280.png"

rrdFile = rrdPath + rrdName
graphPath = rrdPath + graphName

data_sources = ['DS:temperature:GAUGE:600:U:U',
                'DS:humidity:GAUGE:600:U:U',
                'DS:pressure:GAUGE:600:U:U' ]

def getOrCreateRrd():
	if(not os.path.isfile(rrdFile)):
		print "Creating " + rrdFile
 		rrdtool.create( rrdFile,
                '--start', '-10',
                '--step', '1',
                data_sources,
                'RRA:AVERAGE:0.5:1:320000',
                'RRA:MIN:0.5:3600:20000',
                'RRA:MAX:0.5:3600:20000',
                'RRA:AVERAGE:0.5:3600:20000')

def updateGraph(lastUpdated, awsS3Bucket, awsS3Key, graphPath):
	if(time.time() - lastUpdated > 60):
		print "Updating Graph..."
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
				"DEF:temperature_avg=/home/pi/data/bme280.rrd:temperature:AVERAGE:step=3600",
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
				"GPRINT:pressure:LAST:Last\:%5.2lf %s",
				"GPRINT:pressure:AVERAGE:Avg\:%5.2lf %s",
				"GPRINT:pressure:MAX:Max\:%5.2lf %s",
				"GPRINT:pressure:MIN:Min\:%5.2lf %s\\n",
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
	print "Uploading " + fromPath + " to " + "s3:" + targetBucket + "/" + targetKey + " awsAccessKey: " + awsAccessKey + " awsSecretKey: " + awsSecretKey
	conn = S3Connection(awsAccessKey,awsSecretKey)
	bucket = conn.get_bucket(targetBucket)
	k = Key(bucket)
	k.key = targetKey
	k.set_contents_from_filename(fromPath)


def main():
	lastUpdated = 0
	while(1):
		getOrCreateRrd()

		sensor = Bme280Sensor()
		(chip_id, chip_version) = sensor.readBME280ID()
		print "Chip ID     :", chip_id
		print "Version     :", chip_version
		temperature,pressure,humidity = sensor.readBME280All()
		temperature = (temperature * 9/5) + 32
		print "Temperature : ", temperature, "C"
		print "Pressure : ", pressure, "hPa"
		print "Humidity : ", humidity, "%"

		ret = rrdtool.update(rrdFile, '%s:%s:%s:%s' %(time.time(),temperature, humidity, pressure));
		print "Updated RRD ", ret

		lastUpdated = updateGraph(lastUpdated, awsS3Bucket, awsS3Key, graphPath)

		time.sleep(1)

if __name__=="__main__":
   main()