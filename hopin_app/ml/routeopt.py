from haversine import haversine, Unit
import math

sematicweight=0.6
spacialweight=0.4
DESTINATION_RADIUS_KM=0.25

def segmentdistance(rider, startsegment, endsegment):

    # convert to simple cartesian approximation
    riderx, ridery=rider
    startx, starty=startsegment
    endx, endy=endsegment

    startenddiffx=endx-startx
    startenddiffy=endy-starty

    riderstartdiffx=riderx-startx
    riderstartdiffy=ridery-starty

    startendlen=(startenddiffx*startenddiffx)+(startenddiffy*startenddiffy)

    # if starting of segment and ending of segmemt are is same point(you need to only compute with one)
    if startendlen == 0:
        return haversine(rider, startsegment)

    projection=(riderstartdiffx*startenddiffx +
                  riderstartdiffy*startenddiffy)/startendlen
    projection=max(0, min(1, projection))

    closest=(startx + projection*startenddiffx,
               starty + projection*startenddiffy)

    return haversine(rider, closest)


def routesegmentation(rider, routegeometry):

    coords=routegeometry["coordinates"]

    bestindex=None
    minimumdistance=float("inf")

    for i in range(len(coords) - 1):
        # reversing [long,lat] to [lat,long] because haversine expects it like that
        startsegment=(coords[i][1], coords[i][0])
        endsegment=(coords[i+1][1], coords[i+1][0])

        distance=segmentdistance(rider, startsegment, endsegment)

        if distance < minimumdistance:
            minimumdistance=distance
            bestindex=i

    return bestindex, minimumdistance


def proximitycheck(riderlatitude, riderlongitude, ride):

    rider=(riderlatitude, riderlongitude)
    index, distance=routesegmentation(rider, ride.routegeometry)

    if distance > 2.0:  # 2km is the cutoff
        return False, None

    totalsegments=len(ride.routegeometry["coordinates"]) - 1

    if ride.prefereddirection == "to":
        return index < totalsegments,index
    else:
        return index > 0,index


# Haversine's Distance Function- Spacial Score Computation
def haversinefunction(riderlatitude, riderlongitude, routegeometry):

    coordinates=routegeometry["coordinates"]
    minimumdistance=float("inf")

    for driverlongitude, driverlatitude in coordinates:
        distance=haversine((riderlatitude, riderlongitude),
                             (driverlatitude, driverlongitude),
                             unit=Unit.KILOMETERS)

        if distance < minimumdistance:
            minimumdistance=distance

    spatialscore=1/(1+minimumdistance)
    return minimumdistance, spatialscore


def routeoptimization(riderlatitude, riderlongitude, availabletrips):

    finallist=[]
    print("riderlatitude", riderlatitude)
    print("riderlongitude", riderlongitude)
    print("availabletrips", availabletrips)

    for trip in availabletrips:
        value,index=proximitycheck(riderlatitude, riderlongitude, trip)
        if not value:
            continue

        distance, spacialscore=haversinefunction(
            riderlatitude, riderlongitude, trip.routegeometry)

        finallist.append([
            trip,
            distance,
            spacialscore,
            index
        ])

    ranked=sorted(finallist, key=lambda x: x[2], reverse=True)
    # print("Ranked: ",ranked)

    return ranked


def speedcalculation(driverlocation, riderlocation):
    distance=haversine(driverlocation, riderlocation, unit=Unit.KILOMETERS)
    averagespeed=25
    eta=(distance/averagespeed)*60
    return eta


def getriderdropofflocation(ride):
    if ride.trip.prefereddirection=="to":
        return gettripdestination(ride.trip)

    return ride.pickuplatitude, ride.pickuplongitude


def gettripdestination(currenttrip):
    coordinates=(currenttrip.routegeometry or {}).get("coordinates", [])
    if not coordinates:
        return None, None

    destination=coordinates[-1]
    return destination[1], destination[0]


def tripdestinationreached(currenttrip, currentlatitude, currentlongitude, completionradius=DESTINATION_RADIUS_KM):
    if currentlatitude is None or currentlongitude is None:
        return False

    destinationlatitude, destinationlongitude=gettripdestination(currenttrip)
    if destinationlatitude is None or destinationlongitude is None:
        return False

    distance=haversine(
        (currentlatitude, currentlongitude),
        (destinationlatitude, destinationlongitude),
        unit=Unit.KILOMETERS
    )
    return distance<=completionradius


def riderdropped(currentlatitude, currentlongitude, riders):
    dropped_rides = []
    for ride in riders:
        if ride.status=="FULLCONFIRM":
            dropofflatitude, dropofflongitude=getriderdropofflocation(ride)
            if dropofflatitude is None or dropofflongitude is None:
                continue
            distance=haversine((currentlatitude, currentlongitude),(dropofflatitude, dropofflongitude),
                                unit=Unit.KILOMETERS)

            if distance<=DESTINATION_RADIUS_KM:
                ride.status="DROPPED"
                ride.save()
                dropped_rides.append(ride)
                print(f"Ride ended for {ride}")
    return dropped_rides


# Haversine's Distance Function- Price Calculation
def routedistance(routegeometry,startindex,endindex):
    coords=routegeometry["coordinates"]

    if startindex>endindex:
        startindex,endindex=endindex,startindex

    totaldistance=0
    for i in range(startindex,endindex):
        point1=(coords[i][1],coords[i][0])
        point2=(coords[i+1][1],coords[i+1][0])
        totaldistance=totaldistance+haversine(point1,point2,unit=Unit.KILOMETERS)

    return totaldistance

def requestprice(currenttrip,pickupindex,location1):
    totalrouteindex=len(currenttrip.routegeometry["coordinates"]) - 1
    fulltripdistance=routedistance(currenttrip.routegeometry,0,totalrouteindex)

    if currenttrip.prefereddirection=="to":
        startindex=pickupindex
        endindex=totalrouteindex
    else:
        startindex=0
        endindex=pickupindex

    distance=routedistance(currenttrip.routegeometry,startindex,endindex)
    print(distance, "km")

    if fulltripdistance <= 0:
        return 0.0

    price=(distance/fulltripdistance)*currenttrip.price  #proportional fare along the saved route
    price=round(price,2)
    print("Price: ", price)
    return price

def tripprice(routegeometry):
    totalrouteindex=len(routegeometry["coordinates"]) - 1
    distance=routedistance(routegeometry,0,totalrouteindex)
    print(distance, "km")
    price=round(distance*1.3, 2)  # 1.3 rupees per km
    print("Price: ", price)
    return distance, price
