import flask
import requests
from flask import request, jsonify,render_template
from flask_cors import CORS
import sqlite3
import databaseManager
import itinaryCreator
from threading import Thread
import time
import copy


app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

creator = itinaryCreator.itineraryCreator(48.467466, -4.649883)


print("itinaryCreator ready")


@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")



@app.route('/api/docs', methods=['GET'])
def docs():
    return '''<h1>Biken Web API</h1>
<p>Follow the project on <a href="https://github.com/QuentinPhilipp/BikenAPI">Github</a></p>
<hr>
<h3>If start and finish are latitude and longitude</h3>
<p>Endpoint : http://127.0.0.1:5000/api/1.0/itinerary?start=48.577043,7.759002&finish=48.577043,7.759002 DONE
<p>Endpoint : http://127.0.0.1:5000/api/1.0/route?start=48.577043,7.759002&distance={km} WIP

'''

class Compute(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        print("Start Reset")
        creator.resetAllNodes()
        print("End reset")


@app.route('/api/1.0/itinerary', methods=['GET'])
def api_itinerary():
    query_parameters = request.args
    start = query_parameters.get('start')
    finish = query_parameters.get('finish')

    print(start)
    print(finish)

    # If the start/end is an adress
    if start and finish:
        print("Itinerary with address")

        startGeolocalisationTime = time.time();
        startPosition = geocode(start)
        finishPosition = geocode(finish)
        geolocalisationTime = time.time()-startGeolocalisationTime;

        itinerary = creator.getItinerary(startPosition,finishPosition)
        itinerary['geolocalisationTime']=geolocalisationTime;

        print("Time : ",itinerary['calculationTime'])
        # startPosition={"lat": waypointList[0][0], "lon": waypointList[0][1]}
        # finishPosition={"lat": waypointList[-1][0], "lon": waypointList[-1][1]}

        val = {"type" : "itinerary","distance":itinerary['distance'],"geolocalisationTime":itinerary['geolocalisationTime'],"calculationTime":itinerary['calculationTime'], "gps" : "false", "data" : {"startName": start, "startPos": startPosition , "finishName": finish, "finishPos": finishPosition, "waypoints":itinerary["waypoints"]}}
        print("Returned")

        # reset all the nodes in another thread to return the data instantly
        thread_a = Compute()
        thread_a.start()

        return jsonify(val)

    else :
        print("Bad request")
        val = {"error_code": "01", "error_desc": "Endpoint not defined"}
        return jsonify(val)


# Route
@app.route('/api/1.0/route', methods=['GET'])
def api_route():
    query_parameters = request.args
    start = query_parameters.get('start')
    startPos = query_parameters.get('startPos')
    distance = query_parameters.get('distance')

    # If the start is an adress
    if start and distance:
        print("Route with address")
        startPosition = geocode(start)
        val = {"type" : "route", "gps" : "false", "data" : {"startName": start, "startPos": startPosition, "distance": distance, "waypoints":[]}}
        return jsonify(val)

    # If the start is a GPS point
    elif startPos and distance:
        print("Route with GPS points")
        startPosition = extractGPS(startPos)
        val = {"type" : "route", "gps" : "true", "data" : {"startName": start, "startPos": startPosition, "distance": distance, "waypoints":[]}}
        return jsonify(val)
    else :
        print("Bad request")
        val = {"error_code": "01", "error_desc": "Endpoint not defined"}
        return jsonify(val)



@app.route('/api/1.0/debugDownload', methods=['GET'])
def sendDownloadSquares():

    dbManager = databaseManager.DatabaseManager()

    valuesRaw = dbManager.getDownloadPoints()
    values = []
    for point in valuesRaw :
        value = {
        "id":point[0],
        "lat":point[1],
        "lon":point[2]
        }
        values.append(value)

    val = {"status_code": "200", "data": values}
    return jsonify(val)

@app.route('/api/1.0/testThread', methods=['GET'])
def testThread():
    startGeolocalisationTime = time.time();
    start = "Brest"
    finish = "Plougonvelin"
    startPosition = geocode(start)
    finishPosition = geocode(finish)
    thirdPosition = geocode("Plourin")


    geolocalisationTime = time.time()-startGeolocalisationTime;


    list_threads = []

    for i in range(3):
        thread = RouteThread(startPosition,finishPosition,i)
        list_threads.append(thread)

    print("Init done")

    # Start computing
    for thread in list_threads:
        thread.start()

    # Wait the result from all thread
    for thread in list_threads:
        thread.join() # Wait until thread terminates its task

    print("\n\nAll thread complete\n\n")

    # startComputationTime = time.time();
    # itinerary = creator.getItinerary(finishPosition,startPosition)
    # creator.resetAllNodes()
    #
    # itinerary2 = creator.getItinerary(finishPosition,thirdPosition)
    # creator.resetAllNodes()
    #
    # itinerary3 = creator.getItinerary(startPosition,thirdPosition)
    computationTime = time.time()-startComputationTime;

    creator.resetAllNodes()



    itinerary['geolocalisationTime']=geolocalisationTime;
    itinerary['calculationTime']=computationTime;
    print(itinerary)
    print("\n\n\n\n")
    print(itinerary2)


    val = {"type" : "itinerary","distance":itinerary['distance'],"geolocalisationTime":itinerary['geolocalisationTime'],"calculationTime":itinerary['calculationTime'], "gps" : "false", "data" : {"startName": start, "startPos": startPosition , "finishName": finish, "finishPos": finishPosition, "waypoints":itinerary["waypoints"]+itinerary2["waypoints"]+itinerary3["waypoints"]}}

    return val



class RouteThread(Thread):
    def __init__(self,start,finish,id):
        Thread.__init__(self)
        print("Starting initialisation thread",id)
        self.id = id
        self.creator = itinaryCreator.itineraryCreator(48.381571, -3.845928)
        self.startPoint = start
        self.finishPoint=finish
        print("Finish initialisation thread",id)


    def run(self):
        print("Start Computation")
        itineray = self.creator.getItinerary(self.startPoint,self.finishPoint)
        print("End Computation")



def geocode(location):
    # This function use nominatim to get the GPS point of an address
    endpoint = "https://nominatim.openstreetmap.org/search/"
    query = endpoint+location+"?format=json&limit=1"
    response = requests.get(query).json()[0]
    return {"lat": response["lat"], "lon": response["lon"]}

def extractGPS(gpsPoint):
    # Extract latitude and longitude from the request and return in the good format
    position = gpsPoint.split(",")
    return {"lat": position[0], "lon": position[1]}

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

app.run(host='0.0.0.0',port=6060)
