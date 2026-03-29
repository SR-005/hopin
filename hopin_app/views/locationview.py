from ..ml.routeopt import riderdropped, tripdestinationreached
from ..models import trip, riderequest, payment
from django.contrib.auth import get_user_model
import json
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from ..notifications import (
    send_dropoff_notification,
    send_payment_due_notification,
    send_pickup_confirmed_notification,
    send_ride_completed_notification,
)
User=get_user_model()


def rideend(currentride):
    print("Ride status:", currentride.status)

    # Do not complete the ride until at least one passenger has boarded.
    if not currentride.has_boarded:
        return

    reached_trip_destination=tripdestinationreached(currentride,currentride.currentlatitude,currentride.currentlongitude)
    active_rides=riderequest.objects.filter(trip=currentride,status__in=["ACCEPTED", "HALFCONFIRM", "FULLCONFIRM"])

    if currentride.prefereddirection == "from":
        should_complete=reached_trip_destination or not active_rides.exists()
    else:
        should_complete=reached_trip_destination

    if not should_complete:
        return
    
    pendingrides=riderequest.objects.filter(trip=currentride,status="FULLCONFIRM")
    if not pendingrides.exists():
        currentride.status="COMPLETED" 
        currentride.save()

        notboardedriders=riderequest.objects.filter(trip=currentride,status__in=["HALFCONFIRM","ACCEPTED"])
        for riders in notboardedriders:
            if riders.status=="HALFCONFIRM":
                riders.status="DROPPEDNOTCONFIRMED"
            else:
                riders.status="NOTBOARDED"
            riders.save()

        ridecompletedriders=riderequest.objects.filter(trip=currentride,status__in=["DROPPEDNOTCONFIRMED","DROPPED"])
        for riders in ridecompletedriders:
            payment_record, created = payment.objects.get_or_create(
                requestdetails=riders,
                defaults={"amount": riders.price}
            )
            if created:
                send_payment_due_notification(riders.rider, payment_record.id)
            print(f"Payment Request Created for {riders}")
        send_ride_completed_notification(currentride.usercredentials)
        print("Trip Ended")

#fetch location from driver
def updatelocation(request,rideid):
    try:
        print("Entered Function")
        currentride=trip.objects.get(id=rideid, usercredentials=request.user)
        if currentride.status=="COMPLETED":
            return JsonResponse({
                "status": "COMPLETED",
                "message": "Ride ended"
            })
        
        data=json.loads(request.body)
        latitude=data["latitude"]
        longitude=data["longitude"]

        print("Current Latitiude: ",latitude)
        print("Current Longitude: ",longitude)

        currentride.currentlatitude=latitude
        currentride.currentlongitude=longitude
        currentride.lastlocationupdate=timezone.now()
        currentride.save()

        riders=riderequest.objects.filter(trip=currentride,status__in=["FULLCONFIRM", "HALFCONFIRM", "ACCEPTED"])
        print("Current Req2: ",riders)
        dropped_rides=riderdropped(latitude,longitude,riders)
        for dropped_ride in dropped_rides:
            send_dropoff_notification(dropped_ride.rider)
        rideend(currentride)
        return JsonResponse({"status": currentride.status})

    except Exception as e:
        return JsonResponse({
            "status": "ERROR",
            "message": str(e)
        })

#live location fetching from driver
def testlocationfunction(request, rideid):
    currentrequest=None

    ride=get_object_or_404(trip,id=rideid)
    print("Ride Status for Driver: ",ride.status)

    if ride.status!="ONGOING":
        messages.error(request,"This Ride has Successfully been completed")
        return redirect("landing")
    
    currentrequest=riderequest.objects.filter(trip=ride, status__in=["ACCEPTED", "HALFCONFIRM", "FULLCONFIRM", "DROPPED", "DROPPEDNOTCONFIRMED", "NOTBOARDED"])
    print("Current Req1: ",currentrequest)

    if request.method=="POST":
        pickupid=request.POST.get("requestid")
        pickuprider=get_object_or_404(riderequest, id=pickupid, status="ACCEPTED")
        pickuprider.status="HALFCONFIRM"
        pickuprider.save()
        ride.has_boarded=True 
        ride.save()
        send_pickup_confirmed_notification(pickuprider.rider)

    #Context variables added for the new Dashboard UI Navbar
    context={
        "rideid": rideid,
        "riders": currentrequest,
        "status": "true" if request.user.is_authenticated else "false",
        "firstname": request.user.first_name if request.user.is_authenticated else "",
    }

    return render(request, "location.html", context)