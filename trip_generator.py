
import sys
import os.path
import imp
import logging
import logging.handlers
import time

import SocketServer
import socket

import os
import time

#helper
import car_utils
import threading
import random
import linecache
import geopy.distance
import requests
import os

import car_utils

from multiprocessing import Pool
from contextlib import closing

def parseConfigFile(cfile):
	#store config file in dict
	config = {}
	for line in cfile:
		line = line.strip()
		#treat comment
		if not line or line.startswith("#") or line.startswith(";"):
			continue
		if line.startswith("["):
			if not line.endswith("]"):
				LOGGER.error("error: invalid config file")
			else:
				name = line[1:-1] #initiere dict
				config[name] = {}
		else:
			try:
				k, v = line.split(" ", 1);
			except ValueError:
				LOGGER.error("config file contains invalid param!")
				k = line
				v = ""
			try:
				config[name][k] = v
			except TypeError:
				LOGGER.error("invalid char in config",e)
	LOGGER.info("done extracting config to dict")
	return config

def getDistance(coord1,coord2):
	distance = geopy.distance.distance(coord1, coord2).km
	return distance

def getCode(imei_imsi_file):
	#return a random imei or imsi code
	f = open(imei_imsi_file)
	fs = sum(1 for line in f)
	pos = random.randrange(fs)
	code = linecache.getline(imei_imsi_file, int(pos))
	f.close()
	return code

def getSpeed(limit1,limit2):
	speed = round(random.uniform(limit1, limit2), 2)
	print speed
	return speed

LOGGER = logging.Logger('trip-generator-server')
hostname = socket.gethostname()
config_txt = ""

def main():
	here = os.path.dirname(os.path.abspath(__file__))
	os.chdir(here)

	#  set up logger handler
	handler = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	LOGGER.addHandler(handler)
	handler = logging.handlers.RotatingFileHandler(os.path.join(here, 'trip_generator.log'), maxBytes=10*1024*512, backupCount=3)	
	handler.setFormatter(formatter)
	LOGGER.addHandler(handler)
	LOGGER.setLevel(logging.INFO)
	LOGGER.info("hostname: %s", hostname)
	time.sleep(1)
	# done setting up logger

	# call parser conf file
	LOGGER.info("loading config from file ...")
	time.sleep(1)
	config_txt = open("trip_generator.config", "r")
	config = parseConfigFile(config_txt)
	for k,v in config.items():
		print k
		print v
	time.sleep(1)

	###  prepare speed, country and distance
	print ("speed limits:")
	limit1 =  int(config.get("trip_generator.py").get("speed_limit1", "50"))
	limit2 =  int(config.get("trip_generator.py").get("speed_limit2", "130"))
	avg_speed = getSpeed(limit1, limit2)
	# get country
	tara = str(config.get("trip_generator.py").get("countries", "RO"))
	#get Distance
	dist = config.get("trip_generator.py").get("range")
	ruta = list()
	
	# get number of runningcars from config
	no_cars = int(config.get("trip_generator.py").get("vehicles_no", "2"))
	print ("no cars from config:" , no_cars)

	#create list of object type car
	cars = [car_utils.car(tara, avg_speed, dist, route_manual) for i in range(no_cars)]
	thread_list = []
	try:
		LOGGER.info("starting main loop:")
		LOGGER.info("...")
		running = 0
		while (True):
			LOGGER.info("check running cars as configured")
			if no_cars > running :
				for i in range(no_cars):
					cc = threading.Thread(target=cars[i].run) # remove () from run otherwise the thread starts
					cc.daemon = True
					thread_list.append(cc)
					cc.start()
			running_cars = {id(instance): instance.speed for instance in car_utils.car.instances}
			running = len(running_cars)
			time.sleep(5)
	except KeyboardInterrupt:
		print('interrupted!')

if __name__ == "__main__":
	main()
