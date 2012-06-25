# Read temperatures from Arduino board each second and save into a text file

import serial
import time

ser = serial.Serial("COM8",9600,timeout=1)
print "Waiting for Arduino to reset"
time.sleep(2.0)
fp = file(time.strftime("TemperatureSensors_%Y%m%d_%H%M%S.txt",time.localtime()),"w")
try:
    while True:
        ser.write("ta")
        reply = []
        for i in range(6):
            reply.append(100*float(ser.readline()))
        print "%20.3f %8.3f %8.3f %8.3f %8.3f %8.3f %8.3f" % (time.time(),reply[0],reply[1],reply[2],reply[3],reply[4],reply[5])
        print>>fp, "%20.3f %8.3f %8.3f %8.3f %8.3f %8.3f %8.3f" % (time.time(),reply[0],reply[1],reply[2],reply[3],reply[4],reply[5])
        time.sleep(1.0)
finally:
    ser.close()
