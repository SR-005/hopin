from datetime import  time, datetime, timedelta, time
from ..ml.routeopt import routeoptimization,requestprice,routesegmentation
from ..models import trip, riderequest
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .commonview import cleanup
User=get_user_model()


#test rider page function
'''#selectes rides from past that are active again
def rebookable(pastrides):
    preferredtrips=[]
    driveremails=list(pastrides.values_list('trip__usercredentials__email', flat=True).distinct())
    print("Drivers: ",driveremails)

    for driveremail in driveremails:
        driverobject=User.objects.get(email=driveremail)
        activeagain=trip.objects.filter(usercredentials=driverobject,status__in=["EMPTY","ACTIVE"])
        if activeagain.exists():
            preferredtrips.append(activeagain.first())
    return preferredtrips

def requesttimevalidation(request):
    direction=request.POST.get("direction")
    print("TIME: ",request.POST.get("ridetime"))

    ridetime=datetime.strptime(request.POST.get("ridetime"), "%H:%M").time()
    ridedate=datetime.strptime(request.POST.get("ridedate"), "%Y-%m-%d").date()

    #date validation
    today=timezone.localdate()
    now=timezone.localtime().time()
    if ridedate not in [today, today + timedelta(days=1)]:
        messages.error(request, "Rides can only be Requested for Today or Tomorrow")
        return redirect("testrider")
    
    if direction=="to":
        if ridedate==today and now>time(8,0):
            messages.error(request, "Cannot schedule today's 8:00 AM ride after it has passed")
            return redirect("testrider")
        
    #time validation: FROM college (between 1:30PM and 8:00PM)
    elif direction=="from":
        if ridetime<time(13,30) or ridetime>time(20,00):
            messages.error(request, "Rides can only be requested between 1:30PM and 8:00PM")
            return redirect("testrider")
        
        if ridedate==today and ridetime<=now:
            messages.error(request, "Cannot Request a ride in the past")
            return redirect("testrider")
    return 0

#default ride function
def riderdetails1(request):
    requesttimevalidation(request)
    location=request.POST.get("location")
    latitude=request.POST.get("latitude")
    longitude=request.POST.get("longitude")
    direction=request.POST.get("direction")
    date=request.POST.get("ridedate")
    time=request.POST.get("ridetime")

    formatedtime=datetime.strptime(time, "%H:%M")
    lcutofftime=(formatedtime-timedelta(minutes=20)).time()
    ucutofftime=(formatedtime+timedelta(minutes=20)).time()

    request.session["riderlocation"]=location
    request.session["riderlatitude"]=latitude
    request.session["riderlongitude"]=longitude
    print(direction,ucutofftime,lcutofftime,date)     

    #collecting active trip details- for route optimization
    availabletrips=[]
    if direction=="to":
        activetrips=trip.objects.filter(prefereddirection=direction,ridedate=date,status__in=["ACTIVE","EMPTY"],)
    else:
        activetrips=trip.objects.filter(prefereddirection=direction,ridedate=date,ridetime__range=(lcutofftime, ucutofftime),
                                        status__in=["ACTIVE","EMPTY"])
    for trips in activetrips:
        availabletrips.append(trips)

    print("Available Trip Routes: ",availabletrips)
    latitude=float(latitude)
    longitude=float(longitude)

    rides=routeoptimization(latitude,longitude,availabletrips)
    return rides,latitude,longitude

#request for a ride to driver
def requestride(request):
    rideid=request.POST.get("rideid")
    ride=get_object_or_404(trip, id=rideid)

    location=request.session.get("riderlocation")
    latitude=request.session.get("riderlatitude")
    longitude=request.session.get("riderlongitude")
    print(latitude,",",longitude)

    riderequest.objects.create(trip=ride,rider=request.user,pickuplocation=location,pickuplatitude=latitude,pickuplongitude=longitude)
    return redirect("testrider")

#request for a ride previously booked driver
def requestrideagain(request,pastrides):
    tripid=request.POST.get("tripid")
    print("Book Again ID: ",tripid)
    currenttrip=trip.objects.get(id=tripid)
    
    pastride=pastrides.filter(trip__usercredentials=currenttrip.usercredentials).first()

    riderequest.objects.create(trip=currenttrip,rider=request.user,
                               pickuplatitude=pastride.pickuplatitude,pickuplongitude=pastride.pickuplongitude)
    return redirect("testrider")

#cancel an active ride request
def cancelrequest(request):
    print(request.POST.get("requestid"))
    cancelrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    cancelride=cancelrequest.trip
    
    ridedatetime=datetime.combine(cancelride.ridedate, cancelride.ridetime)
    ridedatetime=timezone.make_aware(ridedatetime)
    timeremaining=ridedatetime-timezone.now()
    if timeremaining<=timedelta(minutes=30):
        messages.error(request, "Cannot cancel a ride within 30 minutes of start time.")
        return redirect("testrider")

    if cancelrequest.status=="ACCEPTED":
        print(cancelride.availableseats)
        cancelride.availableseats=cancelride.availableseats+1       #increase trip seats if ride is cancelled after acceptance
        cancelride.save()

    cancelrequest.delete()

    acceptedrequests=riderequest.objects.filter(trip=cancelride,status="ACCEPTED")
    print("AR: ",len(acceptedrequests))

    if len(acceptedrequests)==0:
        cancelride.status="EMPTY"
        cancelride.save()
    
    messages.success(request, "Your Ride Request has been Cancelled!")
    return redirect("testrider")

#fetch all currently ongoing ride requests
def ongoingrequest(allrequest):
    #building a list of ongoing requests
    requestedrides=[]
    ongoing=list(allrequest.values_list("id", flat=True))
    for currentrequest in allrequest:
        if currentrequest.id in ongoing:
            currenttrip=currentrequest.trip
            requestedrides.append(currenttrip.id)
    print("Active Requsted Trip ID: ",requestedrides)
    return requestedrides

#redirect to location tracking page if ride has started
def seemore(request):
    rideid=request.POST.get("tripid")
    print("RideID: ",rideid)
    ride=trip.objects.get(id=rideid)

    if ride.status!="ONGOING":
        messages.error(request, "Driver has not started the ride yet!")
        return redirect("testrider")
    else:
        return redirect("testtracking",rideid=rideid)

#rider page routing function
@login_required
def testriderfunction(request):
    cleanup(request)       #calling cleanup function to delete expired rides
    rides=None
    requests=None
    accepted=None
    requestedrides=None
    latitude=None
    longitude=None
    preferredtrips=None

    allrequest=riderequest.objects.filter(rider=request.user)
    requests=riderequest.objects.filter(rider=request.user, status="PENDING")
    accepted=riderequest.objects.filter(rider=request.user, status="ACCEPTED")
    pastrides=riderequest.objects.filter(rider=request.user, status="DROPPED",paymentdetails__status="PAID")

    preferredtrips=rebookable(pastrides)
    requestedrides=ongoingrequest(allrequest)
    print("Prefered Trips: ",preferredtrips)
    if request.method=="POST":
        action=request.POST.get("action")

        if action=="riderdetails":
            rides,latitude,longitude=riderdetails1(request)
            

        if action=="bookagain":
            return requestrideagain(request,pastrides)

        elif action=="requestride":
            return requestride(request)
        
        elif action=="cancelrequest":
            return cancelrequest(request)
    
        elif action=="seemore":
            return seemore(request)

    return render(request, "testrider.html",{"rides":rides,"requests":requests,"accepted":accepted,"requestedrides":requestedrides,
                                             "pastrides":pastrides,"preferredtrips":preferredtrips,"riderlatitude":latitude,"riderlongitude":longitude})
'''


#------------------------------------------------------RIDER PAGE FUNCTIONS------------------------------------------------------

def rider_poll(request):
    print("Polling..")
    user = request.user
    requests=None
    accepted=None
    requestedrides=None

    requests = riderequest.objects.filter(rider=user, status="PENDING")
    accepted = riderequest.objects.filter(rider=user, status="ACCEPTED")
    requestedrides = ongoingrequest(riderequest.objects.filter(rider=user))

    html = render_to_string("partials/riderpartials.html", {
        "requests": requests,
        "accepted": accepted,
        "requestedrides": requestedrides
    }, request=request)

    return JsonResponse({"html": html,
                            "accepted_ids": list(accepted.values_list("id", flat=True)),
                            "pending_ids": list(requests.values_list("id", flat=True)),
                        })


#selectes rides from past that are active again
def rebookable(pastrides):
    preferredtrips=[]
    driveremails=list(pastrides.values_list('trip__usercredentials__email', flat=True).distinct())
    print("Drivers: ",driveremails)

    for driveremail in driveremails:
        driverobject=User.objects.get(email=driveremail)
        activeagain=trip.objects.filter(usercredentials=driverobject,status__in=["EMPTY","ACTIVE"])
        if activeagain.exists():
            preferredtrips.append(activeagain.first())
    return preferredtrips


def requesttimevalidation(request):
    direction=request.POST.get("direction")
    print("TIME: ",request.POST.get("ridetime"))

    ridetime=datetime.strptime(request.POST.get("ridetime"), "%H:%M").time()
    ridedate=datetime.strptime(request.POST.get("ridedate"), "%Y-%m-%d").date()

    #date validation
    today=timezone.localdate()
    now=timezone.localtime().time()
    if ridedate not in [today, today + timedelta(days=1)]:
        messages.error(request, "Rides can only be Requested for Today or Tomorrow")
        return redirect("rider")
    
    if direction=="to":
        if ridedate==today and now>time(8,0):
            messages.error(request, "Cannot schedule today's 8:00 AM ride after it has passed")
            return redirect("rider")
        
    #time validation: FROM college (between 1:30PM and 8:00PM)
    elif direction=="from":
        if ridetime<time(13,30) or ridetime>time(20,00):
            messages.error(request, "Rides can only be requested between 1:30PM and 8:00PM")
            return redirect("rider")
        
        if ridedate==today and ridetime<=now:
            messages.error(request, "Cannot Request a ride in the past")
            return redirect("rider")
    return 0


#default ride function
def riderdetails(request):
    requesttimevalidation(request)
    location=request.POST.get("location")
    latitude=request.POST.get("latitude")
    longitude=request.POST.get("longitude")
    direction=request.POST.get("direction")
    date=request.POST.get("ridedate")
    time=request.POST.get("ridetime")

    formatedtime=datetime.strptime(time, "%H:%M")
    lcutofftime=(formatedtime-timedelta(minutes=20)).time()
    ucutofftime=(formatedtime+timedelta(minutes=20)).time()

    request.session["riderlocation"]=location
    request.session["riderlatitude"]=latitude
    request.session["riderlongitude"]=longitude
    print(direction,ucutofftime,lcutofftime,date)     

    #collecting active trip details- for route optimization
    availabletrips=[]
    if direction=="to":
        activetrips=trip.objects.filter(prefereddirection=direction,ridedate=date,status__in=["ACTIVE","EMPTY"],)
    else:
        activetrips=trip.objects.filter(prefereddirection=direction,ridedate=date,ridetime__range=(lcutofftime, ucutofftime),
                                        status__in=["ACTIVE","EMPTY"])
    for trips in activetrips:
        availabletrips.append(trips)

    print("Available Trip Routes: ",availabletrips)
    latitude=float(latitude)
    longitude=float(longitude)

    rankedrides=routeoptimization(latitude,longitude,availabletrips)
    rides=[]
    for currenttrip, distance, score, pickupindex in rankedrides:
        print(f"Driver Lat: {currenttrip.latitude}")
        print(f"Driver Lng: {currenttrip.longitude}")
        amount=requestprice(currenttrip,pickupindex,(latitude,longitude))
        print(f"Amount {amount}")
        rides.append((currenttrip, distance, score, amount))

    return rides,latitude,longitude


#request for a ride to driver
def requestride(request):
    if riderequest.objects.filter(rider=request.user,status="ACCEPTED").exists():
        messages.error(request, "You already have an Accepted Ride. Cannot send more Requests")
        return redirect("rider")
    
    rideid=request.POST.get("rideid")
    ride=get_object_or_404(trip, id=rideid)

    location=request.session.get("riderlocation")
    latitude=request.session.get("riderlatitude")
    longitude=request.session.get("riderlongitude")
    print(latitude,",",longitude)

    pickupindex,_=routesegmentation((float(latitude), float(longitude)), ride.routegeometry)
    amount=requestprice(ride,pickupindex,(float(latitude), float(longitude)))

    riderequest.objects.create(
        trip=ride,
        rider=request.user,
        pickuplocation=location,
        pickuplatitude=latitude,
        pickuplongitude=longitude,
        price=amount
    )
    return redirect("rider")


#request for a ride previously booked driver
def requestrideagain(request,pastrides):
    
    if riderequest.objects.filter(rider=request.user,status="ACCEPTED").exists():
        messages.error(request, "You already have an Accepted Ride. Cannot send more Requests")
        return redirect("rider")

    tripid=request.POST.get("tripid")
    print("Book Again ID: ",tripid)
    currenttrip=trip.objects.get(id=tripid)
    
    pastride=pastrides.filter(trip__usercredentials=currenttrip.usercredentials).first()
    location=(float(pastride.pickuplatitude), float(pastride.pickuplongitude))
    pickupindex,_=routesegmentation(location, currenttrip.routegeometry)
    amount=requestprice(currenttrip,pickupindex,location)

    riderequest.objects.create(trip=currenttrip,rider=request.user,
                               pickuplatitude=pastride.pickuplatitude,pickuplongitude=pastride.pickuplongitude,
                               price=amount)
    return redirect("rider")


#cancel an active ride request
def cancelrequest(request):
    print(request.POST.get("requestid"))
    cancelrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    cancelride=cancelrequest.trip
    
    ridedatetime=datetime.combine(cancelride.ridedate, cancelride.ridetime)
    ridedatetime=timezone.make_aware(ridedatetime)
    timeremaining=ridedatetime-timezone.now()
    if timeremaining<=timedelta(minutes=30):
        messages.error(request, "Cannot cancel a ride within 30 minutes of start time.")
        return redirect("rider")

    if cancelrequest.status=="ACCEPTED":
        print(cancelride.availableseats)
        cancelride.availableseats=cancelride.availableseats+1       #increase trip seats if ride is cancelled after acceptance
        cancelride.save()

    cancelrequest.delete()

    acceptedrequests=riderequest.objects.filter(trip=cancelride,status="ACCEPTED")
    print("AR: ",len(acceptedrequests))

    if len(acceptedrequests)==0:
        cancelride.status="EMPTY"
        cancelride.save()
    
    messages.success(request, "Your Ride Request has been Cancelled!")
    return redirect("rider")


#fetch all currently ongoing ride requests
def ongoingrequest(allrequest):
    #building a list of ongoing requests
    requestedrides=[]
    ongoing=list(allrequest.values_list("id", flat=True))
    for currentrequest in allrequest:
        if currentrequest.id in ongoing:
            currenttrip=currentrequest.trip
            requestedrides.append(currenttrip.id)
    print("Active Requsted Trip ID: ",requestedrides)
    return requestedrides



#redirect to location tracking page if ride has started
def seemore(request):
    rideid=request.POST.get("tripid")
    print("RideID: ",rideid)
    ride=trip.objects.get(id=rideid)

    if ride.status!="ONGOING":
        messages.error(request, "Driver has not started the ride yet!")
        return redirect("rider")
    else:
        return redirect("testtracking",rideid=rideid)



#rider page routing function
@login_required
def riderfunction(request):
    cleanup(request)       #calling cleanup function to delete expired rides
    rides=None
    requests=None
    accepted=None
    requestedrides=None
    latitude=None
    longitude=None
    preferredtrips=None

    allrequest=riderequest.objects.filter(rider=request.user)
    requests=riderequest.objects.filter(rider=request.user, status="PENDING")
    accepted=riderequest.objects.filter(rider=request.user, status="ACCEPTED")
    pastrides=riderequest.objects.filter(rider=request.user, status="DROPPED",paymentdetails__status="PAID")

    preferredtrips=rebookable(pastrides)
    requestedrides=ongoingrequest(allrequest)
    print("Prefered Trips: ",preferredtrips)
    if request.method=="POST":
        action=request.POST.get("action")

        if action=="riderdetails":
            rides,latitude,longitude=riderdetails(request)
            

        if action=="bookagain":
            return requestrideagain(request,pastrides)

        elif action=="requestride":
            return requestride(request)
        
        elif action=="cancelrequest":
            return cancelrequest(request)
    
        elif action=="seemore":
            return seemore(request)

    return render(request, "rider.html",{"rides":rides,"requests":requests,"accepted":accepted,"requestedrides":requestedrides,
                                             "pastrides":pastrides,"preferredtrips":preferredtrips,"riderlatitude":latitude,"riderlongitude":longitude})
