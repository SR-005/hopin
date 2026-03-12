from haversine import haversine, Unit

sematicweight=0.6
spacialweight=0.4

#Haversine's Distance Function- Price Calculation
def price(location1,location2):
    distance=haversine(location1, location2)    #calculating distance between two locations (in km)
    print(distance,"km")
    price=round(distance*1.3)       #1.3 rupees per km
    print("Price: ",price)
    return price

#Haversine's Distance Function- Spacial Score Computation
def haversinefunction(riderlatitude,riderlongitude,routegeometry):

    coordinates=routegeometry["coordinates"]
    minimumdistance=float("inf")

    for driverlongitude,driverlatitude in coordinates:
        distance=haversine((riderlatitude,riderlongitude),
                           (driverlatitude,driverlongitude),
                           unit=Unit.KILOMETERS)
        
        if distance<minimumdistance:
            minimumdistance=distance

    spatialscore=1/(1+minimumdistance)
    return minimumdistance,spatialscore

def finalscore(riderlatitude,riderlongitude,availabletrips):

    finallist=[]
    print("riderlatitude",riderlatitude)
    print("riderlongitude",riderlongitude)
    print("availabletrips",availabletrips)

    for trip in availabletrips:
        distance,spacialscore=haversinefunction(riderlatitude,riderlongitude,trip.routegeometry)

        finallist.append([
            trip,
            distance,
            spacialscore
        ])

    ranked = sorted(finallist, key=lambda x: x[2], reverse=True)
    #print("Ranked: ",ranked)

    return ranked

def rideend(currentlatitude,currentlongitude,route):
    coordinates=route["coordinates"]
    destination=coordinates[-1]
    destinationlatitude=destination[1]
    destinationlongitude=destination[0]

    completionradius=0.05
    distance=haversine((currentlatitude,currentlongitude),
                           (destinationlatitude,destinationlongitude),
                           unit=Unit.KILOMETERS)
    
    if distance>=completionradius:
        print("Ride Ended")
    return 0

'''finalscore("via pipeline",[["via main road",(10.1071868,76.3597351)],["via high court",(10.1265,76.3533)],  
                           ["via pipeline road",(10.1071868,76.3597351)],["via pipeline road",(10.0463,76.3242)]])  #aluva,pulinchode,aluva,hmt'''