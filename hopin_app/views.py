from .forms import signupForm, loginForm, createtripForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

import json
from datetime import date,time,datetime,timedelta
from .models import userdetail, trip, riderequest
from .ml.routeopt import finalscore

from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.


#------------------------------------------------------LANDING PAGE FUNCTIONS------------------------------------------------------
# Main Landing Page View
def landingfunction(request):
    user = None
    username=None
    firstname=None
    try:
        print("Current User Email: ", request.user.email)
        if request.user.email!=None:
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
    if request.method == "POST":

        loginform = loginForm(request.POST)
        if loginform.is_valid():
            useremail = loginform.cleaned_data["email"]
            userpassword = loginform.cleaned_data["password"]
            print(useremail, userpassword)

            user = authenticate(request, username=useremail,password=userpassword)
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
    if request.method == "POST":
        # collect values from html form and validate it w.r.t signupForm
        signupform = signupForm(request.POST)
        if signupform.is_valid():
            firstname = signupform.cleaned_data["first_name"]
            lastname = signupform.cleaned_data["last_name"]
            useremail = signupform.cleaned_data["email"]
            userpassword = signupform.cleaned_data["password"]

            # create_user is a Django Built in function to create a User to User Model
            newuser = User.objects.create_user(email=useremail, password=userpassword)
            newuser.first_name = firstname
            newuser.last_name = lastname
            newuser.save()
            messages.success(request, "Account has been successfully created.")

            user = authenticate(request, username=useremail,password=userpassword)
            login(request, user)
            return redirect("landing")

        else:
            for errors in signupform.errors.items():  # returns a tuple of errors from the form
                # we use indexing to catch the exact error message from tuple
                messages.error(request, errors[1][0])
    return render(request, "signup.html")


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
        else:
            print("Form not Valid")
            print(request.POST)

#accept a ride request
def acceptride(request):
    print("ACCEPT")
    currentrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    currentride=currentrequest.trip
    
    if currentride.availableseats>0:
        currentrequest.status="ACCEPTED"
        currentrequest.save()

        currentride.availableseats=currentride.availableseats-1
        currentride.save()
    else:
        print("SEAT FULL!!")

#reject a ride request
def rejectride(request):
    print("REJECT")
    currentrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    currentrequest.status="REJECTED"
    currentrequest.save()

#delete a posted ride
def deleteride(request):
    print("DELETEING RIDE")
    deleteride=trip.objects.get(id=request.POST.get("tripid"))
    deleteride.delete()

#driver page routing function
def testdriverfunction(request):
    requests=None
    accepted=None
    lasttrip=None
    startride=False

    #fetch trips of the current user
    try:
        lasttrip=trip.objects.get(usercredentials=request.user)
        if lasttrip.status!="ONGOING":
            
            currenttime = timezone.localtime()
            ridetime = datetime.combine(lasttrip.ridedate, lasttrip.ridetime)
            ridetime = timezone.make_aware(ridetime)
            starttime = ridetime - timedelta(minutes=30)
            print("C: ",currenttime)
            print("S: ",starttime)
            if currenttime>=starttime:
                print("It's time to Start")
                startride=True

        requests=riderequest.objects.filter(trip=lasttrip,status="PENDING")
        accepted=riderequest.objects.filter(trip=lasttrip,status="ACCEPTED")
    except Exception as e:
        print(e)

    action=request.POST.get("action")
    if action=="tripdetails":
        tripdetails(request)
    elif action=="accept":
        acceptride(request)
    elif action=="reject":
        rejectride(request)
    elif action=="delete":
        deleteride(request)

    return render(request, "testdriver.html",{"requests":requests,"accepted":accepted,"lasttrip": lasttrip,"startride":startride})


#------------------------------------------------------RIDER PAGE FUNCTIONS------------------------------------------------------
#default ride function
def riderdetails(request):
    location=request.POST.get("location")
    latitude=request.POST.get("latitude")
    longitude=request.POST.get("longitude")
    direction=request.POST.get("direction")

    print(location,latitude,longitude,direction)     

    #collecting active trip details- for route optimization
    availabletrips=[]
    activetrips=trip.objects.filter(status="ACTIVE")
    for trips in activetrips:
        availabletrips.append(trips)

    print("Available Trip Routes: ",availabletrips)
    latitude=float(latitude)
    longitude=float(longitude)

    rides=finalscore(latitude,longitude,availabletrips)
    return rides

#request for a ride to driver
def requestride(request):
    rideid=request.POST.get("rideid")
    ride=get_object_or_404(trip, id=rideid)
    riderequest.objects.create(trip=ride,rider=request.user)
    return 0

#cancel an active ride request
def cancelrequest(request):
    cancelrequest=riderequest.objects.get(id=request.POST.get("requestid"))
    cancelride=cancelrequest.trip
    if cancelrequest.status=="ACCEPTED":
        print(cancelride.availableseats)
        cancelride.availableseats=cancelride.availableseats+1       #increase trip seats if ride is cancelled after acceptance
        cancelride.save()
    cancelrequest.delete()

#clean up expired rides
def cleanup(request):
    unengagedtrips=trip.objects.filter(status="ACTIVE")
    now=timezone.localtime()

    for trips in unengagedtrips:
        ridedatetime=datetime.combine(trips.ridedate, trips.ridetime)
        ridedatetime=timezone.make_aware(ridedatetime)

        if ridedatetime < now:
            trips.delete()

    return 0

#rider page routing function
def testriderfunction(request):
    cleanup(request)       #calling cleanup function to delete expired rides
    rides=None
    requests=None
    accepted=None
    requestedrides=None

    allrequest=riderequest.objects.filter(rider=request.user)
    requests=riderequest.objects.filter(rider=request.user, status="PENDING")
    accepted=riderequest.objects.filter(rider=request.user, status="ACCEPTED")
    
    if request.method=="POST":
        action=request.POST.get("action")

        if action=="riderdetails":
            rides=riderdetails(request)

            #building a list of ongoing requests
            requestedrides=[]
            ongoing=list(allrequest.values_list("id", flat=True))
            for currentrequest in allrequest:
                if currentrequest.id in ongoing:
                    currenttrip=currentrequest.trip
                    requestedrides.append(currenttrip.id)
            print("Active Requsted Trip ID: ",requestedrides)


        elif action=="requestride":
            requestride(request)
        elif action=="cancelrequest":
            cancelrequest(request)

    return render(request, "testrider.html",{"rides":rides,"requests":requests,"accepted":accepted,"requestedrides":requestedrides})







def testlocationfunction(request):
    return render(request, "testlocation.html")