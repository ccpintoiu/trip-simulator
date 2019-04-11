##
# Cosminp
# helper for trip_generator server

import requests
import os
import json
import datetime
import time
import geopy.distance
import random
import linecache
from kafka import KafkaProducer
import sys
import threading



class car(object):
	instances = [] # keep count
	def __init__(self, country, speed, distance, route):
		self.country = country
		self.speed = speed
		self.distance = distance
		self.route = route # test purpose only
		car.instances.append(self) # add instances 
        
	def getRoute(self):
		# gets route with api call
		# we also check if distance is valid.
    r = requests.get("http://176.223.250.98:8005/api/v1/getRoute/"+self.country)
		routee = json.loads(r.content)
		dist = json.dumps(routee["dist"])
		c=0
		while (dist > self.distance) and (c<4):
			if (dist < self.distance) and (c<4):
				self.route = r.content
				print("FOUND route! distance is: " + dist)
				return self.route
				break
			else:
				print("no route with suitable distance was found, trying again " + dist) # replace with raise excpt
			if (dist > self.distance) and (c>=3):
				sys.exit("Error message: no route found! exit now!")

			r = requests.get("http://176.223.250.98:8005/api/v1/getRoute/"+self.country)
			routee = json.loads(r.content)
			dist = json.dumps(routee["dist"])
			print ("distance from route : ",c," ", dist)
			c+=1


	def distance_kill(self): # should be deleted.
		# case route distance is bigger, kill instance 
		routee = json.loads(self.route)
		print routee
		dist = json.dumps(routee["dist"])
		print dist
		if self.distance < dist:
			print ("stopping car: ")
			print self
			del self # should recall route 

	def getSpeed(self):
		return round(random.uniform(50, 130), 2)

	def timestamp(self):
		print 'Car starting at: {0}'.format(datetime.datetime.now())
		return time.time()

	def getDistance(self,coord1,coord2):
		# coords_1 = (52.2296756, 21.0122287)
		# coords_2 = (52.406374, 16.9251681)
		distance = geopy.distance.distance(coord1, coord2).km
		#print distance
		return distance

	def getCode(self, imei_imsi_file):
		f = open(imei_imsi_file)
		fs = sum(1 for line in f)
		pos = random.randrange(fs)
		code = linecache.getline(imei_imsi_file, int(pos))
		f.close()
		#print(code)
		return code

	def getKafkaProducer(self):	
		# get a connection to kafka broker
		# kafka-topics --zookeeper localhost:2181 --create --topic trips --partitions 2 --replication-factor 2
		#producer = None
		try:
			producer = KafkaProducer(bootstrap_servers='instance-38635.bigstep.io:9092')
		except Exception as e:
			print (" connection to kafka failed")
			print (str(e))
		finally:
			return producer

	def strip_coords(self,pair):
		# strip and prepare coords pair for finding distance
		strip_pair = pair.lstrip("\"[").rstrip("]\"").replace(" ", "")
		return tuple(strip_pair.split(','))


	def sendPosition(self):
		#to do: load coords list from json 
		self.getRoute()
		print ("--------------- send location-------------")
		self.timestamp()
		#Latitude , Longitude, Speed, Distance, Timestamp, IMEI, IMSI
		imei = self.getCode("/opt/Route_apps/IMEI.csv") # to do: move in constr
		imsi = self.getCode("/opt/Route_apps/IMSI.csv") # 
		route = json.loads(self.route)

		#### send first position:
		pos_start = json.dumps(route["start"])
		pst = self.strip_coords(pos_start)
		first_stop = json.dumps(route["inter"][0])
		dis = self.getDistance(pst,self.strip_coords(first_stop))

		tokafka1 = {}
		tokafka1 = {
		"Latitude": pst[0],
		"Longitude": pst[1],
		"Speed": self.speed,
		"Distance": dis,
		"Timestamp": time.time(),
		"IMEI": imei,
		"IMSI": imsi
		}

		print tokafka1
		producer = self.getKafkaProducer()
		producer.send('trips', json.dumps(tokafka1).encode('utf-8'))
		print (" !!! good idea to start console consumer: kafka-console-consumer --zookeeper <host>:2181 --bootstrap-server <host>:9092 --topic trips --from-beginning")
		print ("starting point / message sent to kafka broker: success")

		#get number of way points:
		for i in range (1,len(route['inter'])):
			#print i
			next_stop = json.dumps(route["inter"][i])
			inter = self.strip_coords(next_stop)
			dis = self.getDistance(pst,self.strip_coords(next_stop))
			tokafka_n = {}

			tokafka_n = { "Latitude": inter[0], "Longitude": inter[1], "Speed": self.getSpeed(), "Distance": dis, "Timestamp": time.time(), "IMEI": imei, "IMSI": imsi }
			#print tokafka_n
			# wait before sending next location to get there (should be *100)
			time_i = dis / float(self.getSpeed())
			#print ("time: "),time_i,(" h")
			time.sleep(time_i)
			producer.send('trips', json.dumps(tokafka_n).encode('utf-8'))
			#print ("intermeriary point / message sent to kafka broker", i)

		#to do: send last location:
		print ("last point / message sent to kafka broker for this car")
		pos_stop = json.dumps(route["stop"])
		pstop = self.strip_coords(pos_stop)
		dis = self.getDistance(self.strip_coords(next_stop),pstop)

		tokafka_N = {}
		tokafka_N = {
		"Latitude": pstop[0],
		"Longitude": pstop[1],
		"Speed": self.speed,
		"Distance": dis,
		"Timestamp": time.time(),
		"IMEI": imei,
		"IMSI": imsi
		}

		producer.close()
		del self

	def run(self):
		r = threading.Thread(target=self.sendPosition)
		r.daemon = True
		r.start()

		




























