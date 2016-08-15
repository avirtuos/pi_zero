# pi_zero
This repo is mostly a collection of tutorials built around the raspberry pi zero.

![alt tag](https://raw.githubusercontent.com/avirtuos/pi_zero/master/doc/img/pi_zero_pinout.jpg)

# Pi Zero... Pros... & Cons...


# Pi Zero Setup

This section will walk you through installing an OS on your PiZero. This instalation procedure is based on Adafruit's guide, their wiki has imensely helpful to many of my projects. I encourage everyone to check it out and support them.

## Step 1 - OS Imaging

Download Raspberry-PI-SD-Installer-OS-X from <a href='https://github.com/RayViljoen/Raspberry-PI-SD-Installer-OS-X'>this git repo.</a>

> Ray Vijoen has created a useful script to handle much of the sdcard formating and initial installation for you on MACthat makes it really easy to make an SD card using a Mac.

Alteranatively, you can use a <a href='http://www.tweaking4all.com/software/macosx-software/macosx-apple-pi-baker/'>Apple Pi Baker</a> to setup your SD card, and make backups once you have your Pi setup the way you like.

## Step 2 - Initial Wiring

Connect a USB Hub to an <a href='https://www.amazon.com/Adapter-Samusung-Android-Windows-Function/dp/B00LN3LQKQ'>OTG</a> Cable that goes to your Pi's Micro USB OTG Port. The plug your USB Wifi Dongle and Keyboard into the hub. Now you are ready to power up your Pi via the other micro USB port.  Lastly, plug in your mini-HDMI to HDMI adapter as well as your HDMI cable for your monitor/tv.

## Step 3 - Initial Configuration

Power on your Pi and once the loging prompt appears log in using the username: pi and the password: raspberry. You'll want to change the password at some point but I'll leave that up to you to decide. Once you are at the command prompt you'll want to setup the wifi so we can switch to using SSH instead of having the pi cabled directly to our monitor and keyboard.

You can do this by editing /etc/network/interfaces via the following command:

`sudo nano /etc/network/interfaces`

You may need to edit your keyboard mappings if you notice that the double quotes you type show up as @-signs. This can be done by running `sudo dpkg-reconfigure keyboard-configuration` and following the instructions to switch to a US keyboard. This will mostly likely require a reboot to take affect fully (it did for me).



# Parts List

Here you can find all the parts used throughout these tutorials, I've tried to mark the ones that are required for the basics vs ones for special projects.

* <a href='https://www.amazon.com/Adapter-Samusung-Android-Windows-Function/dp/B00LN3LQKQ'>A USB OTG Cable (~$5)</a> - Required For All Tutorials
* <a href='https://www.amazon.com/Sabrent-4-Port-Individual-Switches-HB-UMLS/dp/B00BWF5U0M'>A USB Hub (~$7)</a> - Required For All Tutorials but may not be needed after initial configuration.
* <a href='https://www.amazon.com/Edimax-EW-7811Un-150Mbps-Raspberry-Supports/dp/B003MTTJOY'>USB Wifi Dongle (~$9)</a> - Networked Projects Only
* <a href='https://www.amazon.com/Rii-Wireless-Keyboard-mini-X1/dp/B00I5SW8MC'>USB Keyboard (~$17)</a> - Required for initial setup. I prefer this small one because I use it for many projects just to get SSH up and running then I use my regulard computer.
* <a href='https://www.amazon.com/gp/product/B00MU2YPXO'>Mini HDMI to Female HDMI (~$10)</a> - Required for initial setup unless the project drives a display continually.

