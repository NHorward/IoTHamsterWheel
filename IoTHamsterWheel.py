# Harold the Hamster
# Nicole Horward 2018

# Sources:
# Inspiration:
# http://www.instructables.com/id/Track-How-Far-Your-Hamster-Runs/
#
# ThingSpeak:
# https://community.thingspeak.com/tutorials/update-a-thingspeak-channel-using-mqtt-on-a-raspberry-pi/
#
# Magnetic door sensor:
# https://learn.adafruit.com/adafruits-raspberry-pi-lesson-12-sensing-movement/overview
#
# LCD Screen:
# https://learn.adafruit.com/character-lcds
# https://www.raspberrypi-spy.co.uk/2012/07/16x2-lcd-module-control-using-python/
#
# Scheduler:
# https://stackoverflow.com/questions/22715086/scheduling-python-script-to-run-every-hour-accurately
# https://apscheduler.readthedocs.io/en/latest/userguide.html#configuring-the-scheduler
# https://schedule.readthedocs.io/en/stable/
#
# Autorun script on startup of Raspberry Pi:
# https://www.raspberrypi.org/documentation/linux/usage/rc-local.md


# Import libraries
from __future__ import print_function
import time
import datetime
import schedule
import paho.mqtt.publish as publish
import RPi.GPIO as io
io.setmode(io.BCM)

print("Hi, this is a tracker for Harold the Hamster")

#Setup the pins of the Raspberry
# Pin for the wheel
wheelpin = 17
# Setup wheel pin
io.setup(wheelpin, io.IN, pull_up_down=io.PUD_UP)

# Pins for the LCD Screen
# Register Select
lcdRs = 7
# Enable or Strobe
lcdE = 8
# Data pins
lcdData4 = 25
lcdData5 = 24
lcdData6 = 23
lcdData7 = 18
# Setup LCD Pins
io.setup(lcdE, io.OUT)
io.setup(lcdRs, io.OUT)
io.setup(lcdData4, io.OUT)
io.setup(lcdData5, io.OUT)
io.setup(lcdData6, io.OUT)
io.setup(lcdData7, io.OUT)

#LCD Constants
# Characters per line
lcdWidth = 16
lcdChr = True
lcdCmd = False
# LCD Ram address 1st line
lcdLine1 = 0x80
# LCD Ram address 2nd line
lcdLine2 = 0xC0
# Timing
lcdPulse = 0.0005
lcdDelay = 0.0005

# Circumferance of Harold's wheel
# 18cm diameter * PI = 56.52 cm = 0.5652 m = 0.0005652 km
wheelsize = 0.0005652

# Number of wheel rotations
rotations = 0

# Distance covered in hamsterwheel
distance = 0

# Daily distance
# Distance covered in hamsterwheel to be displayed on LCD screen
# Reset to 0 every day at 0:00
dailyDistance = 0

# Speed
speed = 0

# Set the starttime to now
starttime = datetime.datetime.now()

#  ThingSpeak Channel Settings

# The ThingSpeak Channel ID
# Replace this with your Channel ID
channelID = "YourChannelID"

# The Write API Key for the channel
# Replace this with your Write API key
apiKey = "YourAPIKey"

#  MQTT Connection Methods
# Set useUnsecuredTCP to True to use the default MQTT port of 1883
# This type of unsecured MQTT connection uses the least amount of system resources.
useUnsecuredTCP = False

# Set useUnsecuredWebSockets to True to use MQTT over an unsecured websocket on port 80.
# Try this if port 1883 is blocked on your network.
useUnsecuredWebsockets = False

# Set useSSLWebsockets to True to use MQTT over a secure websocket on port 443.
# This type of connection will use slightly more system resources, but the connection
# will be secured by SSL.
useSSLWebsockets = True

# The Hostname of the ThinSpeak MQTT service
mqttHost = "mqtt.thingspeak.com"

# Set up the connection parameters based on the connection type
if useUnsecuredTCP:
    tTransport = "tcp"
    tPort = 1883
    tTLS = None

if useUnsecuredWebsockets:
    tTransport = "websockets"
    tPort = 80
    tTLS = None

if useSSLWebsockets:
    import ssl
    tTransport = "websockets"
    tTLS = {'ca_certs':"/etc/ssl/certs/ca-certificates.crt",'tls_version':ssl.PROTOCOL_TLSv1}
    tPort = 443

# Create the topic string
topic = "channels/" + channelID + "/publish/" + apiKey

# LCD Screen setup
def lcdByte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command

    io.output(lcdRs, mode)  # RS

    # High bits
    io.output(lcdData4, False)
    io.output(lcdData5, False)
    io.output(lcdData6, False)
    io.output(lcdData7, False)
    if bits & 0x10 == 0x10:
        io.output(lcdData4, True)
    if bits & 0x20 == 0x20:
        io.output(lcdData5, True)
    if bits & 0x40 == 0x40:
        io.output(lcdData6, True)
    if bits & 0x80 == 0x80:
        io.output(lcdData7, True)

    # Toggle 'Enable' pin
    lcdToggleEnable()

    # Low bits
    io.output(lcdData4, False)
    io.output(lcdData5, False)
    io.output(lcdData6, False)
    io.output(lcdData7, False)
    if bits & 0x01 == 0x01:
        io.output(lcdData4, True)
    if bits & 0x02 == 0x02:
        io.output(lcdData5, True)
    if bits & 0x04 == 0x04:
        io.output(lcdData6, True)
    if bits & 0x08 == 0x08:
        io.output(lcdData7, True)

    # Toggle 'Enable' pin
    lcdToggleEnable()


def lcdToggleEnable():
    # Toggle enable
    time.sleep(lcdDelay)
    io.output(lcdE, True)
    time.sleep(lcdPulse)
    io.output(lcdE, False)
    time.sleep(lcdDelay)


# Initialise LCD Display
lcdByte(0x33,lcdCmd) # 110011 Initialise
lcdByte(0x32,lcdCmd) # 110010 Initialise
lcdByte(0x06,lcdCmd) # 000110 Cursor move direction
lcdByte(0x0C,lcdCmd) # 001100 Display On,Cursor Off, Blink Off
lcdByte(0x28,lcdCmd) # 101000 Data length, number of lines, font size
lcdByte(0x01,lcdCmd) # 000001 Clear display
time.sleep(lcdDelay)

def lcdShowMessage(message, line):
    # Send string to display

    message = message.ljust(lcdWidth, " ")

    lcdByte(line, lcdCmd)

    for i in range(lcdWidth):
        lcdByte(ord(message[i]), lcdChr)

# Reset the wheel measurements
def resetValues():
    global distance
    global speed
    global rotations
    print ('Before reset', distance, 'km', speed, 'km/h', rotations, 'rotations')
    distance = 0
    speed = 0
    rotations = 0
    print ('After reset', distance, 'km', speed, 'km/h', rotations, 'rotations')
    
def resetDailyValues():
    global dailyDistance
    dailyDistance = 0

# Send IoT message to Thingspeak
def sendMessage():
    print("Hello, I'm a message!")
    print ('Minute Update', distance, 'km', speed, 'km/h', rotations, 'rotations')
    # build the payload string
    tPayload = "field1=" + str(rotations) + "&field2=" + str(distance) + "&field3=" + str(speed)
    resetValues()
    # attempt to publish this data to the topic
    try:
        publish.single(topic, payload=tPayload, hostname=mqttHost, port=tPort, tls=tTLS, transport=tTransport)
        

    except:
        print("There was an error while publishing the data.")


# Send a message every minute
schedule.every().minutes.do(sendMessage)
# Reset the daily values at midnight
schedule.every().day.at("0:00").do(resetDailyValues)


# Function to calculate the current speed of the hamster wheel
def calculateSpeed(spintime):
    seconds = spintime.days * 24 * 60 * 60 + spintime.seconds + spintime.microseconds / 1000000.
    currentSpeed = wheelsize / (seconds/60./60.)
    return currentSpeed

# While the script runs
while True:
        # Check the pending scheduled tasks
        schedule.run_pending()
        # Show the daily covered distance on the first line of the LCD
        lcdShowMessage(str(dailyDistance)+"Km", lcdLine1)
        # Show the current speed on the second line of the LCD
        lcdShowMessage(str(speed)+ "Km/h", lcdLine2)

        # When the magnet passes the magnet reed switch, one rotation has happened
        if (io.input(wheelpin) == 0):
            # The end of the rotation is now
            endtime = datetime.datetime.now()
            # The time spent spinning was the endtime - starttime
            spintime = endtime - starttime
            # New starttime is the endtime
            starttime = endtime
            # Calculating the speed based on the spintime
            speed = calculateSpeed(spintime)
            # Calculating the distance covered
            distance = distance + wheelsize
            dailyDistance = dailyDistance + wheelsize
            # Calculating the amount of rotations
            rotations += 1
            # Print to console and sleep
            print (distance, 'km', speed, 'km/h', rotations, 'rotations')
            time.sleep(0.1)


