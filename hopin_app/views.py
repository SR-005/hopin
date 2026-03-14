from .forms import signupForm, loginForm, createtripForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse

import json
from datetime import date,time,datetime,timedelta
from .models import userdetail, trip, riderequest
from .ml.routeopt import finalscore,rideend

from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.


#------------------------------------------------------LANDING PAGE FUNCTIONS------------------------------------------------------
# Main Landing Page View
def landingfunction(request):
    user=None
    username=None
    firstname=None
    try:
        print("Current User Email: ", request.user.email)
        if request.user.email!=None:
            user=request.user
            status="true"
        username=User.objects.get(email=request.user.email)
        username=str(username.first_name).upper()
        username=username.split()
        firstname=username[0]
    except:
        print("User is not Logged in or Logged Out")
        status="false"

    return render(request, "landing.html", {"status":status,"user":user,"firstname":firstname})

# Main Logout Function
def logoutfunction(request):
    logout(request)
    messages.success(request, "User Logged Out- Log back in to use the app!")
    return redirect("/")

# Main Login Page View
def loginfunction(request):
    if request.method=="POST":

        loginform=loginForm(request.POST)
        if loginform.is_valid():
            useremail=loginform.cleaned_data["email"]
            userpassword=loginform.cleaned_data["password"]
            print(useremail, userpassword)

            user=authenticate(request, username=useremail,password=userpassword)
            if user is not None:
                login(request, user)
                messages.success(request, "Login Successfull!!")
                return redirect("landing")
            else:
                messages.error(request, "Invalid Credentials!!")
        else:
            print(loginform.errors)
    return render(request, "login.html")

# Main Sign Up Page View
def signupfunction(request):
    if request.method=="POST":
        # collect values from html form and validate it w.r.t signupForm
        signupform=signupForm(request.POST)
        if signupform.is_valid():
            firstname=signupform.cleaned_data["first_name"]
            lastname=signupform.cleaned_data["last_name"]
            useremail=signupform.cleaned_data["email"]
            userpassword=signupform.cleaned_data["password"]

            # create_user is a Django Built in function to create a User to User Model
            newuser=User.objects.create_user(email=useremail, password=userpassword)
            newuser.first_name=firstname
            newuser.last_name=lastname
            newuser.save()
            messages.success(request, "Account has been successfully created.")

            user=authenticate(request, username=useremail,password=userpassword)
            login(request, user)
            return redirect("landing")

        else:
            for errors in signupform.errors.items():  # returns a tuple of errors from the form
                # we use indexing to catch the exact error message from tuple
                messages.error(request, errors[1][0])
    return render(request, "signup.html")


def riderfunction(request):
    return render(request, "rider.html")


#---------------------------------------------------------COMMON FUNCTIONS---------------------------------------------------------
#clean up expired rides
def cleanup(request):
    unengagedtrips=trip.objects.filter(status="EMPTY")
    now=timezone.localtime()

    for trips in unengagedtrips:
        ridedatetime=datetime.combine(trips.ridedate, trips.ridetime)
        ridedatetime=timezone.make_aware(ridedatetime)

        if ridedatetime < now:
            trips.delete()

    return 0





#---------------------------------------------------------LOCATION FUNCTIONS---------------------------------------------------------
#to set location to show rider where currently driver is
def fetchtracking(request,rideid):
    currentride=trip.objects.get(id=rideid)
    print("Tracked Latitiude: ",currentride.currentlatitude)
    print("Tracked Longitude: ",currentride.currentlongitude)
    return JsonResponse({
        "lat": currentride.currentlatitude,
        "lng": currentride.currentlongitude,
        "route": json.dumps(currentride.routegeometry),
        "status": currentride.status,
    })

def confirmride(request):
    rideid=request.POST.get("tripid")
    currentride=trip.objects.get(id=rideid)
    currentrequest=riderequest.objects.get(trip=currentride,rider=request.user)
    print("REQ: ",currentrequest)
    currentrequest.status="CONFIRM"
    currentrequest.save()
    return redirect("testtracking",rideid=rideid)

#to render tracking page
def testtrackingfunction(request,rideid):
    currentrideid=None
    currentride=get_object_or_404(trip, id=rideid, status="ONGOING")
    currentrideid=rideid
    
    currentrequest=riderequest.objects.get(trip=currentride,rider=request.user,status__in=["ACCEPTED", "CONFIRM"])
    riderlatitude=currentrequest.pickuplatitude
    riderlongitude=currentrequest.pickuplongitude

    if request.method=="POST":
        action=request.POST.get("action")
        if action=="confirmride":
            return confirmride(request)

    return render(request, "testtracking.html",{"rideid":currentrideid,"riderlatitude":riderlatitude,"riderlongitude":riderlongitude})

#live location fetching from driver
def testlocationfunction(request,rideid):
    ride=get_object_or_404(trip, id=rideid, status="ONGOING")
    if request.method=="POST":
        data=json.loads(request.body)
        latitude=data["latitude"]
        longitude=data["longitude"]

        print("Current Latitude: ",latitude)
        print("Current Longitude: ",longitude)

        currentride=trip.objects.get(usercredentials=request.user, status="ONGOING")
        currentride.currentlatitude=latitude
        currentride.currentlongitude=longitude
        currentride.lastlocationupdate=timezone.now()      #fetches current time
        currentride.save()

        route=route = currentride.routegeometry
        status=rideend(latitude,longitude,route)
        if status==True:
            '''currentride.status="COMPLETED"
            currentrequest=riderequest.objects.get(trip=currentride,status="ACCEPTED")
            currentrequest.status="COMPLETED"

            currentride.save()
            currentrequest.save()'''
            print("Ride Ended")
    return render(request, "testlocation.html",{"rideid":rideid})





#------------------------------------------------------DRIVER PAGE FUNCTIONS------------------------------------------------------
#Trip time validation
def tripdatetimevalidation(request):
    direction=request.POST.get("prefereddirection")
    print("TIME: ",request.POST.get("ridetime"))

    ridetime=datetime.strptime(request.POST.get("ridetime"), "%H:%M").time()
    ridedate = datetime.strptime(request.POST.get("ridedate"), "%Y-%m-%d").date()

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
            newtrip = createtripform.save(commit=False)
            newtrip.usercredentials=request.user
                
            #make ride geometry into JSON format for db storage
            routegeometry=json.loads(request.POST.get("routegeometry"))
            newtrip.routegeometry=routegeometry

            newtrip.save()
            return redirect("testdriver")
        else:
            print("Form not Valid")
            print(request.POST)
            return redirect("testdriver")

#accept a ride request
def acceptride(request):
    print("ACCEPT")
    currentrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    currentride=currentrequest.trip
    rider=currentrequest.rider
    
    if currentride.availableseats>0:
        currentrequest.status="ACCEPTED"
        currentrequest.save()

        currentride.availableseats=currentride.availableseats-1
        
        if currentride.status=="EMPTY":
            currentride.status="ACTIVE"
            currentride.save()

        riderequest.objects.filter(rider=rider).exclude(id=currentrequest.id).delete()

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
    ride=trip.objects.get(id=rideid)

    ride.status="ONGOING"
    ride.save()
    return redirect("testlocation", rideid=rideid)

#driver page routing function
def testdriverfunction(request):
    cleanup(request)       #calling cleanup function to delete expired rides
    requests=None
    accepted=None
    lasttrip=None
    startride=True

    #fetch trips of the current user
    try:
        lasttrip=trip.objects.get(usercredentials=request.user)
        '''if lasttrip.status!="ONGOING":
            
            currenttime = timezone.localtime()
            ridetime = datetime.combine(lasttrip.ridedate, lasttrip.ridetime)
            ridetime = timezone.make_aware(ridetime)
            starttime = ridetime - timedelta(minutes=30)
            print("C: ",currenttime)
            print("S: ",starttime)
            if currenttime>=starttime:
                print("It's time to Start")
                startride=True'''

        requests=riderequest.objects.filter(trip=lasttrip,status="PENDING")
        accepted=riderequest.objects.filter(trip=lasttrip,status="ACCEPTED")
    except Exception as e:
        print(e)

    action=request.POST.get("action")
    if action=="tripdetails":
        return tripdetails(request)
    elif action=="accept":
        return acceptride(request)
    elif action=="reject":
        return rejectride(request)
    elif action=="delete":
        return deleteride(request)
    elif action=="startride":
        return starttracking(request)

    return render(request, "testdriver.html",{"requests":requests,"accepted":accepted,"lasttrip": lasttrip,"startride":startride})





#------------------------------------------------------RIDER PAGE FUNCTIONS------------------------------------------------------

def requesttimevalidation(request):
    direction=request.POST.get("direction")
    print("TIME: ",request.POST.get("ridetime"))

    ridetime=datetime.strptime(request.POST.get("ridetime"), "%H:%M").time()
    ridedate = datetime.strptime(request.POST.get("ridedate"), "%Y-%m-%d").date()

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
def riderdetails(request):
    requesttimevalidation(request)
    location=request.POST.get("location")
    latitude=request.POST.get("latitude")
    longitude=request.POST.get("longitude")
    direction=request.POST.get("direction")
    date=request.POST.get("ridedate")
    time=request.POST.get("ridetime")

    formatedtime=datetime.strptime(time, "%H:%M")
    ucutofftime=(formatedtime-timedelta(minutes=20)).time()
    lcutofftime=(formatedtime+timedelta(minutes=20)).time()

    request.session["riderlatitude"]=latitude
    request.session["riderlongitude"]=longitude
    print(location,latitude,longitude,direction)     

    #collecting active trip details- for route optimization
    availabletrips=[]
    if direction=="to":
        activetrips=trip.objects.filter(status__in=["ACTIVE","EMPTY"],prefereddirection=direction,ridedate=date)
    else:
        activetrips=trip.objects.filter(status__in=["ACTIVE","EMPTY"],prefereddirection=direction,ridedate=date,
                                        ridetime__range=(lcutofftime, ucutofftime))
    for trips in activetrips:
        availabletrips.append(trips)

    print("Available Trip Routes: ",availabletrips)
    latitude=float(latitude)
    longitude=float(longitude)

    rides=finalscore(latitude,longitude,availabletrips)
    return rides,latitude,longitude

#request for a ride to driver
def requestride(request):
    rideid=request.POST.get("rideid")
    ride=get_object_or_404(trip, id=rideid)

    latitude=request.session.get("riderlatitude")
    longitude=request.session.get("riderlongitude")
    print(latitude,",",longitude)

    riderequest.objects.create(trip=ride,rider=request.user,pickuplatitude=latitude,pickuplongitude=longitude)
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
def testriderfunction(request):
    cleanup(request)       #calling cleanup function to delete expired rides
    rides=None
    requests=None
    accepted=None
    requestedrides=None
    latitude=None
    longitude=None

    allrequest=riderequest.objects.filter(rider=request.user)
    requests=riderequest.objects.filter(rider=request.user, status="PENDING")
    accepted=riderequest.objects.filter(rider=request.user, status="ACCEPTED")
    pastrides=riderequest.objects.filter(rider=request.user, status="COMPLETED")
    
    if request.method=="POST":
        action=request.POST.get("action")

        if action=="riderdetails":
            rides,latitude,longitude=riderdetails(request)

            #building a list of ongoing requests
            requestedrides=[]
            ongoing=list(allrequest.values_list("id", flat=True))
            for currentrequest in allrequest:
                if currentrequest.id in ongoing:
                    currenttrip=currentrequest.trip
                    requestedrides.append(currenttrip.id)
            print("Active Requsted Trip ID: ",requestedrides)

        elif action=="requestride":
            return requestride(request)
        
        elif action=="cancelrequest":
            return cancelrequest(request)
    
        elif action=="seemore":
            return seemore(request)

    return render(request, "testrider.html",{"rides":rides,"requests":requests,"accepted":accepted,"requestedrides":requestedrides,
                                             "pastrides":pastrides,"riderlatitude":latitude,"riderlongitude":longitude})






