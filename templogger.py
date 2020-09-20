# -*- coding: utf-8 -*-
import os
import glob
import argparse
import time
import datetime
import sys
from influxdb import InfluxDBClient

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# add more sensor variables here based on your setup

temp=['sensor code','tttttttttt','ddddddddddd','ssssssssss']
base_dir = '/sys/bus/w1/devices/'

device_folders = glob.glob(base_dir + '28*')

snum=1 #Number of connected temperature sensors

# Set required InfluxDB parameters.
# (this could be added to the program args instead of beeing hard coded...)
host = "192.168.0.18" #Could also use local ip address like "192.168.1.136"
port = 8086
user = "root"
password = "root"

# Sample period (s).
# How frequently we will write sensor data from the temperature sensors to the database.
sampling_period = 5

def read_temp_raw(device_file): 
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(device_file): # checks the temp recieved for errors
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        # set proper decimal place for C
        temp = float(temp_string) / 1000.0
        # Round temp to 2 decimal points
        temp = round(temp, 1)
    # value of temp might be unknown here if equals_pos == -1
    return temp

def get_args():
    '''This function parses and returns arguments passed in'''
    # Assign description to the help doc
    parser = argparse.ArgumentParser(description='Program writes measurements data from the connected DS18B20 to specified influx db.')
    # Add arguments
    parser.add_argument(
        '-db','--database', type=str, help='Database name', required=True)
    parser.add_argument(
        '-sn','--session', type=str, help='Session', required=True)
    now = datetime.datetime.now()
    parser.add_argument(
        '-rn','--run', type=str, help='Run number', required=False,default=now.strftime("%Y%m%d%H%M"))
    
    # Array of all arguments passed to script
    args=parser.parse_args()
    # Assign args to variables
    dbname=args.database
    runNo=args.run
    session=args.session
    return dbname, session,runNo
    
def get_data_points():
    # Get the three measurement values from the DS18B20 sensors
    for sensors in range (snum): # change number of sensors based on your setup
        device_file=device_folders[sensors]+ '/w1_slave'
        temp[sensors] = read_temp(device_file)
        print (device_file,sensors,temp[sensors])
    # Get a local timestamp
    timestamp=datetime.datetime.utcnow().isoformat()
    
    # Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1)
    datapoints = [
        {
            "measurement": session,
            "tags": {"runNum": runNo,},
            "time": timestamp,
            "fields": {"temperature 1":temp[0]}
        }
        ]
    return datapoints

# Match return values from get_arguments()
# and assign to their respective variables
dbname, session, runNo =get_args()   
print ("Session: ", session)
print ("Run No: ", runNo)
print ("DB name: ", dbname)

# Initialize the Influxdb client
client = InfluxDBClient(host, port, user, password, dbname)
        
try:
     while True:
        # Write datapoints to InfluxDB
        datapoints=get_data_points()
        bResult=client.write_points(datapoints)
        print("Write points {0} Bresult:{1}".format(datapoints,bResult))
            
        # Wait for next sample
        time.sleep(sampling_period)
        
        # Run until keyboard ctrl-c
except KeyboardInterrupt:
    print ("Program stopped by keyboard interrupt [CTRL_C] by user. ")

