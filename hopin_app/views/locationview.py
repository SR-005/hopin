from ..ml.routeopt import riderdropped
from ..models import trip, riderequest, payment
from django.contrib.auth import get_user_model
import json
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
User=get_user_model()


def rideend(currentride):
    print("Ride status:", currentride.status)
    if not currentride.has_boarded:
        return
    
    pendingrides=riderequest.objects.filter(trip=currentride,status="FULLCONFIRM")
    if not pendingrides.exists() and currentride.has_boarded:
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
            payment.objects.create(requestdetails=riders,amount=riders.price)
            print(f"Payment Request Created for {riders}")
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
        riderdropped(latitude,longitude,riders)
        rideend(currentride)
        return JsonResponse({"status": currentride.status})

    except Exception as e:
        return JsonResponse({
            "status": "ERROR",
            "message": str(e)
        })

#live location fetching from driver
def testlocationfunction(request,rideid):
    currentrequest=None

    ride=get_object_or_404(trip, id=rideid)
    print("Ride Status for Driver: ",ride.status)

    if ride.status != "ONGOING":
        messages.error(request, "This Ride has Successfully been completed")
        return redirect("landing")
    
    currentrequest=riderequest.objects.filter(trip=ride, status__in=["ACCEPTED", "HALFCONFIRM","FULLCONFIRM","DROPPED", "DROPPEDNOTCONFIRMED", "NOTBOARDED"])
    print("Current Req1: ",currentrequest)

    if request.method=="POST":
        pickupid=request.POST.get("requestid")
        pickuprider=get_object_or_404(riderequest, id=pickupid, status="ACCEPTED")
        pickuprider.status="HALFCONFIRM"
        pickuprider.save()

    return render(request,"testlocation.html",{"rideid":rideid,"riders":currentrequest})


def testlocationfunction(request, rideid):
    currentrequest = None

    ride = get_object_or_404(trip, id=rideid)
    print("Ride Status for Driver: ", ride.status)

    if ride.status != "ONGOING":
        messages.error(request, "This Ride has Successfully been completed")
        return redirect("landing")
    
    currentrequest = riderequest.objects.filter(trip=ride, status__in=["ACCEPTED", "HALFCONFIRM", "FULLCONFIRM", "DROPPED", "DROPPEDNOTCONFIRMED", "NOTBOARDED"])
    print("Current Req1: ", currentrequest)

    if request.method == "POST":
        pickupid = request.POST.get("requestid")
        pickuprider = get_object_or_404(riderequest, id=pickupid, status="ACCEPTED")
        pickuprider.status = "HALFCONFIRM"
        pickuprider.save()
        ride.has_boarded = True 
        ride.save()

    # --- NEW: Context variables added for the UI Navbar ---
    context = {
        "rideid": rideid,
        "riders": currentrequest,
        # Pass status as "true" or "false" string so the JS in the template reads it correctly
        "status": "true" if request.user.is_authenticated else "false",
        # Pass the user's first name for the top right profile display
        "firstname": request.user.first_name if request.user.is_authenticated else "",
    }

    return render(request, "testlocation.html", context)