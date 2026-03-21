from haversine import haversine, Unit
import math

sematicweight=0.6
spacialweight=0.4

#Haversine's Distance Function- Price Calculation
def price(location1,location2):
    distance=haversine(location1, location2)    #calculating distance between two locations (in km)
    print(distance,"km")
    price=round(distance*1.3)       #1.3 rupees per km
    print("Price: ",price)
    return price



def segmentdistance(rider, startsegment, endsegment):

    # convert to simple cartesian approximation
    riderx,ridery=rider
    startx,starty=startsegment
    endx,endy=endsegment

    startenddiffx = endx-startx
    startenddiffy = endy-starty

    riderstartdiffx=riderx-startx
    riderstartdiffy=ridery-starty

    startendlen=(startenddiffx*startenddiffx)+(startenddiffy*startenddiffy)

    #if starting of segment and ending of segmemt are is same point(you need to only compute with one)
    if startendlen==0:
        return haversine(rider, startsegment)

    projection=(riderstartdiffx*startenddiffx + riderstartdiffy*startenddiffy)/startendlen
    projection=max(0, min(1, projection))

    closest=(startx + projection*startenddiffx, starty + projection*startenddiffy)

    return haversine(rider, closest)


def routesegmentation(rider,routegeometry):

    coords=routegeometry["coordinates"]

    bestindex=None
    minimumdistance=float("inf")

    for i in range(len(coords) - 1):
        startsegment=(coords[i][1], coords[i][0])       #reversing [long,lat] to [lat,long] because haversine expects it like that  
        endsegment=(coords[i+1][1], coords[i+1][0])     

        distance=segmentdistance(rider, startsegment, endsegment)

        if distance<minimumdistance:
            minimumdistance=distance
            bestindex=i

    return bestindex, minimumdistance


def proximitycheck(riderlatitude,riderlongitude,ride):

    rider=(riderlatitude,riderlongitude)

    index,distance=routesegmentation(rider, ride.routegeometry)

    if distance>2.0:      #2km is the cutoff
        return False

    totalsegments=len(ride.routegeometry["coordinates"]) - 1

    if ride.prefereddirection == "to":
        return index<totalsegments
    else:
        return index>0


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

def routeoptimization(riderlatitude,riderlongitude,availabletrips):

    finallist=[]
    print("riderlatitude",riderlatitude)
    print("riderlongitude",riderlongitude)
    print("availabletrips",availabletrips)

    for trip in availabletrips:
        if not proximitycheck(riderlatitude,riderlongitude,trip):
            continue
         
        distance,spacialscore=haversinefunction(riderlatitude,riderlongitude,trip.routegeometry)

        finallist.append([
            trip,
            distance,
            spacialscore
        ])

    ranked = sorted(finallist, key=lambda x: x[2], reverse=True)
    #print("Ranked: ",ranked)

    return ranked

def riderdropped(currentlatitude,currentlongitude,riders):
    completionradius=0.05
    for ride in riders:
        if ride.status=="FULLCONFIRM":
            distance=haversine((currentlatitude,currentlongitude),(ride.pickuplatitude,ride.pickuplongitude), unit=Unit.KILOMETERS)
    
            if distance<=completionradius:
                ride.status="DROPPED"
                ride.save()
                print(f"Ride ended for {ride}")
