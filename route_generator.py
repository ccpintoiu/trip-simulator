
import tempfile
import random
import geocoder
import linecache
import openrouteservice
import flask
import json
from flask import Flask, jsonify, request
from openrouteservice.directions import directions
import geopy.distance
import os
from os import environ
from sklearn.externals import joblib
from flask import Flask, jsonify, request
import json

# Specify your personal API key (OSM api key)
client = openrouteservice.Client(key='') 

# return city coordonates after randomly selecting a city
def getCityCoords(country, cityfile):
	f = open(cityfile)
	filesize = sum(1 for line in f)
	pos = random.randrange(filesize)
	print pos
	start_pos = linecache.getline(cityfile, int(pos))
	f.close()
	print(start_pos)
	g = geocoder.osm(start_pos)
	pair = (float(g.latlng[1]), float(g.latlng[0]))
	print ("coordonates: ", pair)
	return pair

# returns route b2een cities (list)
# req start stop coords
def getRoute(client,coords):
	routes_W = directions(client, coords, maneuvers=True)
	parsed_data = json.dumps(routes_W)
	json_object = json.loads(parsed_data)
	way=list()
	for i in range (0,len(json_object['routes'][0]['segments'][0]['steps']) - 1):
		parsed_data_way = json.dumps(routes_W['routes'][0]['segments'][0]['steps'][i]['maneuver']['location'])
		way.append(parsed_data_way)
	return way

# returns distance given coordonates
import geopy.distance
def getDistance(coord1,coord2):
	distance = geopy.distance.distance(coord1, coord2).km
	return distance

# now create a simple api 
app = Flask(__name__)

@app.route("/api/v1/getRoute/<string:country>", methods=['GET'])
def api_all(country):
	if request.method == 'GET':
		client = openrouteservice.Client(key='') 
		start = getCityCoords(country)
		stop = getCityCoords(country)
		coords = (start , stop)
		response = getRoute(client, coords)
		distance = getDistance(start,stop)
		print ("distance: ",distance)
		out_smart = {
		"start": start,
		"inter": tuple(response),
		"stop": stop,
  		"dist": distance
  		}
   return json.dumps(out_smart)

if __name__ == "__main__":
    port = int(environ.get('PORT', port))
    app.run(host='IP', port=port, debug=True)
