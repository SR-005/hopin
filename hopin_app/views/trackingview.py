from ..ml.routeopt import speedcalculation
from ..models import trip, riderequest
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
User = get_user_model()


# ---------------------------------------------------------LOCATION FUNCTIONS---------------------------------------------------------
# to set location to show rider where currently driver is
def fetchtracking(request, rideid):
    currentride = trip.objects.get(id=rideid)
    requestid = request.GET.get("requestid")
    if not requestid:
        return JsonResponse({"error": "Missing requestid"}, status=400)
    currentrequest = riderequest.objects.get(id=requestid)
    print("Request Status: ", currentrequest)

    if currentrequest.status in ["DROPPED", "DROPPEDNOTCONFIRMED", "NOTBOARDED"] or currentride.status == "COMPLETED":
        messages.success(request, "Ride completed successfully")
        return JsonResponse({
            "redirect": True,
            "url": "/"
        })

    driverlocation = (currentride.currentlatitude,
                      currentride.currentlongitude)
    riderlocation = (currentrequest.pickuplatitude,
                     currentrequest.pickuplongitude)
    try:
        eta = speedcalculation(driverlocation, riderlocation)
    except:
        eta = 0

    print("Tracked Latitiude: ", currentride.currentlatitude)
    print("Tracked Longitude: ", currentride.currentlongitude)
    print("ETA: ", eta)

    return JsonResponse({
        "lat": currentride.currentlatitude, "lng": currentride.currentlongitude,
        "route": currentride.routegeometry, "status": currentride.status,
        "eta": round(eta)
    })


def fetchstatus(request, requestid):
    currentrequest = riderequest.objects.get(id=requestid)
    return JsonResponse({
        "status": currentrequest.status
    })


def testconfirmride(request):
    requestid = request.POST.get("requestid")
    requestid = request.POST.get("requestid")
    currentrequest = riderequest.objects.get(id=requestid)

    currentrequest.status = "FULLCONFIRM"
    currentrequest.save()

    currentrequest.trip.has_boarded = True
    currentrequest.trip.save()

    return redirect("testtracking", rideid=request.POST.get("tripid"))

# to render tracking page


def testtrackingfunction(request, rideid):
    currentrideid = None
    currentride = get_object_or_404(
        trip, id=rideid, status__in=["ONGOING", "COMPLETED"])
    print("Current Tracking Ride: ", currentride)
    currentrideid = rideid

    currentrequest = riderequest.objects.get(trip=currentride, rider=request.user, status__in=[
                                             "ACCEPTED", "HALFCONFIRM", "FULLCONFIRM", "DROPPED"])
    riderlatitude = currentrequest.pickuplatitude
    riderlongitude = currentrequest.pickuplongitude

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirmride":
            return testconfirmride(request)

    return render(request, "testtracking.html", {"rideid": currentrideid, "requestid": currentrequest.id, "riderlatitude": riderlatitude, "riderlongitude": riderlongitude})


def confirmride(request):
    requestid = request.POST.get("requestid")
    requestid = request.POST.get("requestid")
    currentrequest = riderequest.objects.get(id=requestid)

    currentrequest.status = "FULLCONFIRM"
    currentrequest.save()

    currentrequest.trip.has_boarded = True
    currentrequest.trip.save()

    return redirect("tracking", rideid=request.POST.get("tripid"))

# to render tracking page


def trackingfunction(request, rideid):
    currentrideid = None
    currentride = get_object_or_404(
        trip, id=rideid, status__in=["ONGOING", "COMPLETED"])
    print("Current Tracking Ride: ", currentride)
    currentrideid = rideid

    currentrequest = riderequest.objects.get(trip=currentride, rider=request.user, status__in=[
                                             "ACCEPTED", "HALFCONFIRM", "FULLCONFIRM", "DROPPED"])
    riderlatitude = currentrequest.pickuplatitude
    riderlongitude = currentrequest.pickuplongitude

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirmride":
            return confirmride(request)

    return render(request, "tracking.html", {"rideid": currentrideid, "requestid": currentrequest.id, "riderlatitude": riderlatitude, "riderlongitude": riderlongitude})
