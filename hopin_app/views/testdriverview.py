from datetime import  time, datetime, timedelta, time
from ..models import trip, riderequest
from ..ml.routeopt import tripprice
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.template.loader import render_to_string

import json
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from ..forms import createtripForm

from .commonview import cleanup
User=get_user_model()

#driver html poll
@login_required
def driverpoll(request):
    activetrips=trip.objects.filter(usercredentials=request.user,status__in=["ACTIVE", "EMPTY"]).first()
    requests=list(riderequest.objects.filter(trip=activetrips,status="PENDING").select_related("trip", "rider"))
    accepted=list(riderequest.objects.filter(trip=activetrips, status="ACCEPTED").select_related("trip", "rider"))
    startride=True

    for currentrequest in requests:
        currentrequest.routegeometry_json=json.dumps(currentrequest.trip.routegeometry or {})

    for currentrequest in accepted:
        currentrequest.routegeometry_json=json.dumps(currentrequest.trip.routegeometry or {})

    html=render_to_string("partials/driverincoming.html", {
        "requests": requests,
        "accepted": accepted,
        "activetrips": activetrips
    }, request=request)


    return JsonResponse({
        "html": html,
        "pending_ids": [currentrequest.id for currentrequest in requests],
        "accepted_ids": [currentrequest.id for currentrequest in accepted],
    })



#Trip time validation
def tripdatetimevalidation(request):
    direction=request.POST.get("prefereddirection")
    print("TIME: ",request.POST.get("ridetime"))

    ridetime=datetime.strptime(request.POST.get("ridetime"), "%H:%M").time()
    ridedate=datetime.strptime(request.POST.get("ridedate"), "%Y-%m-%d").date()

    #date validation
    today=timezone.localdate()
    now=timezone.localtime().time()
    if ridedate not in [today, today + timedelta(days=1)]:
        messages.error(request, "Rides can only be scheduled for Today or Tomorrow")
        return redirect("testdriver")

    #time validation: TO college (before 8:00AM)
    if direction=="to":
        if ridetime<time(7,00):
            messages.error(request, "Rides can only be scheduled from 7:00AM")
            return redirect("testdriver")
        elif ridetime>time(8,00):
            messages.error(request, "Rides must arrive at college at 8:00 AM")
            return redirect("testdriver")
        
        if ridedate==today and now>time(8,0):
            messages.error(request, "Cannot schedule today's 8:00 AM ride after it has passed")
            return redirect("testdriver")
        
    #time validation: FROM college (between 1:30PM and 8:00PM)
    elif direction=="from":
        if ridetime<time(13,30) or ridetime>time(20,00):
            messages.error(request, "Rides must be scheduled between 1:30PM and 8:00PM")
            return redirect("testdriver")
        
        if ridedate==today and ridetime<=now:
            messages.error(request, "Cannot schedule a ride in the past")
            return redirect("testdriver")
    return None

#create new trip
def tripdetails(request):
    if request.method=="POST":
        createtripform=createtripForm(request.POST)
        if createtripform.is_valid():
            #ride time validation
            datetimevalid=tripdatetimevalidation(request)
            if datetimevalid:
                return datetimevalid
            
            # commit=False: saves the form content but doesnot upload it into db yet
            newtrip=createtripform.save(commit=False)
            newtrip.usercredentials=request.user
                
            #make ride geometry into JSON format for db storage
            routegeometry=json.loads(request.POST.get("routegeometry"))
            newtrip.routegeometry=routegeometry

            helmetavailable=request.POST.get("helmet")
            newtrip.helmet=helmetavailable

            latitude=float(request.POST.get("latitude"))
            longitude=float(request.POST.get("longitude"))
            distance,amount=tripprice(routegeometry)

            newtrip.distance=distance
            newtrip.price=amount


            newtrip.save()
            return redirect("testdriver")
        else:
            print("Form not Valid")
            print(request.POST)
            return redirect("testdriver")

#accept a ride request
def acceptride(request):
    print("ACCEPT")
    try:
        currentrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    except:
        messages.error(request, "Ride Request has been Withdrawn!!")
        return redirect("testdriver")
    currentride=currentrequest.trip
    rider=currentrequest.rider
    
    if currentride.availableseats>0:
        currentrequest.status="ACCEPTED"
        currentrequest.save()

        currentride.availableseats=currentride.availableseats-1
        print(currentride.availableseats)
        if currentride.status=="EMPTY":
            currentride.status="ACTIVE"
            currentride.save()

        riderequest.objects.filter(rider=rider,status="PENDING").exclude(id=currentrequest.id).delete()

        currentride.save()
        return redirect("testdriver")
    else:
        messages.error(request, "Ride Max Capacity has already been filled!")
        return redirect("testdriver")

#reject a ride request
def rejectride(request):
    print("REJECT")
    currentrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    currentrequest.status="REJECTED"
    currentrequest.save()
    return redirect("testdriver")

#delete a posted ride
def deleteride(request):
    print("DELETEING RIDE")
    deleteride=trip.objects.get(id=request.POST.get("tripid"))

    ridedatetime=datetime.combine(deleteride.ridedate, deleteride.ridetime)
    ridedatetime=timezone.make_aware(ridedatetime)
    timeremaining=ridedatetime-timezone.now()

    if timeremaining<=timedelta(minutes=20):
        messages.error(request, "Cannot delete ride within 20 minutes of start time.")
        return redirect("testdriver")

    deleteride.delete()
    messages.success(request, "Your Ride has been Deleted!")
    return redirect("testdriver")


def starttracking(request):
    rideid=request.POST.get("tripid")
    print("RIDE ID:", rideid)
    ride=trip.objects.get(id=rideid)

    ride.status="ONGOING"
    ride.save()
    return redirect("testlocation", rideid=rideid)

#driver page routing function
@login_required
def testdriverfunction(request):
    cleanup(request)       #calling cleanup function to delete expired rides
    requests=None
    accepted=None
    lasttrip=None
    startride=True
    activetrips=None
    #fetch trips of the current user
    try:
        lasttrip=trip.objects.filter(usercredentials=request.user,status="COMPLETED").order_by("-id").first()
        activetrips=trip.objects.filter(usercredentials=request.user,status__in=["ACTIVE", "EMPTY"]).first()
        print("ACTIVE: ",activetrips)
        print("PAST: ",lasttrip)
        '''if lasttrip.status!="ONGOING":
            
            currenttime=timezone.localtime()
            ridetime=datetime.combine(lasttrip.ridedate, lasttrip.ridetime)
            ridetime=timezone.make_aware(ridetime)
            starttime=ridetime - timedelta(minutes=30)
            print("C: ",currenttime)
            print("S: ",starttime)
            if currenttime>=starttime:
                print("It's time to Start")
                startride=True'''

    except Exception as e:
        print(e)

    action=request.POST.get("action")
    print("ACTION: ",action)
    if action=="tripdetails":
        notallowed=trip.objects.filter(usercredentials=request.user,status__in=["EMPTY","ACTIVE","ONGOING"]).exists()
        if notallowed:
            messages.error(request, "Cannot Create Two Rides at Once!!")
            return redirect("testdriver")
        return tripdetails(request)
    elif action=="accept":
        return acceptride(request)
    elif action=="reject":
        return rejectride(request)
    elif action=="delete":
        return deleteride(request)
    elif action=="startride":
        return starttracking(request)

    pendingrequests=list(riderequest.objects.filter(trip=activetrips,status="PENDING").select_related("trip", "rider"))
    acceptedrequests=list(riderequest.objects.filter(trip=activetrips,status="ACCEPTED").select_related("trip", "rider"))
    lasttriproutegeometryjson=json.dumps(lasttrip.routegeometry) if lasttrip and lasttrip.routegeometry else ""

    for currentrequest in pendingrequests:
        currentrequest.routegeometry_json=json.dumps(currentrequest.trip.routegeometry or {})

    for currentrequest in acceptedrequests:
        currentrequest.routegeometry_json=json.dumps(currentrequest.trip.routegeometry or {})

    return render(request, "testdriver.html",{"requests":pendingrequests,
                                              "accepted":acceptedrequests,
                                              "lasttrip": lasttrip,"startride":startride,
                                              "activetrips":activetrips,
                                              "ongoing":trip.objects.filter(usercredentials=request.user,status="ONGOING").order_by("-id").first(),
                                              "lasttrip_routegeometry_json": lasttriproutegeometryjson})
