#BME280 - A Pi Zero IOT Platform
This is a tutorial for how you can use a DHT11 Temperature and Humidity sensor along with RRDTool and AWS S3.

*This tutorial assumes you've already setup your Pi for wifi and also for i2c using my previous tutorials.

Here is a live example of what our little Pi Zero is capable of. 

<center>![alt tag](http://virtuoso-iot.s3-website-us-east-1.amazonaws.com/images/pi_139_bme280.png)</center>

## Parts List

* <a href='https://www.amazon.com/Digital-Humidity-Temperature-Sensor-Arudino/dp/B007YE0SB6'>4x DHT11 Digital Humidity and Temperature Sensor (~$8 - you only need 1 but this is a 4 pack)</a>

## Step 1 - Software Setup

Install our pre-requisite software, namely RRDTool and SMBus.

`sudo apt-get install python-smbus python-boto python-rrdtool rrdtool python-pip`

and then install tendo for our singleton support

`pip install tendo`

## Step 2 - Wire Our DHT11 to VDD, GND, and GPIO.

Since we've walked through this in a previous tutorial, I won't repeat every step. Here is an image of how to wire up both the pi and the DHT11 via i2c.

<center>![alt tag](https://raw.githubusercontent.com/avirtuos/pi_zero/master/doc/img/pi_zero_pinout_zoom.png)</center>

Once you have it wired up, we can run i2c probe to see if our sensor is detected.


## Step 3 - Setup Our IOT Python Script

Grab a copy of the tutorial's python scripts my <a href='https://github.com/avirtuos/pi_zero/tree/master/dht11'>GitHub - DHT11 Tutorial</a>.

You'll want to take a close look at dht11_collectd.py as this script requires a few settings, namely. Your AWS Access Key, AWS Secret Key, and the location in S3 to post the graphs to.

These configs are easily configured via environment variable to collectd.py

export NODE_NAME="pi_154_bme280"
export AWS_ACCESS_KEY="XYZ"
export AWS_SECRETE_KEY="XYZ"
export AWS_BUCKET="XYZ"
export HTTP_PORT="8000"
/home/pi/projects/pi_zero/dht11/dht11_collectd.py

You can disable the embedded web server which makes the rrd graphs available over http by not setting the HTTP_PORT env variable. Similarly, ommitting the AWS environment variables will disable upload of the graphs to S3.

This script uses RRDTool to store up to 5 years of 1 minute, avg, min, and max data for our sensors. It also retains 48 hours of 1 second data since it samples our sensors once a second.

## Step 4 - Finished

If we update the graph every 5 minutes we can expect this to cost us ~ $0.52 cents a year in S3 costs. It will be tough to find a cheeper hosting option :)

And best of all, we get to keep our data and control visualizations, unlike services like ThingSpeak, Nest, EcoBee, etc...

