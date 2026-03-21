from .forms import signupForm, loginForm, createtripForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse

import razorpay
import json
import os
from dotenv import load_dotenv
from datetime import date,time,datetime,timedelta
from .models import userdetail, trip, riderequest,payment
from .ml.routeopt import routeoptimization,riderdropped

from django.contrib.auth import get_user_model
User = get_user_model()


load_dotenv()
RAZORID=os.getenv("RAZORPAYKEY")
RAZORSECRET=os.getenv("RAZORPAYSECRET")
razorpayclient=razorpay.Client(auth=(RAZORID,RAZORSECRET))

# Create your views here.

#------------------------------------------------------PAYMENT PAGE FUNCTIONS------------------------------------------------------

def averagerating(currentrequest):
    driver=currentrequest.trip.usercredentials
    driverdetails=userdetail.objects.get(usercredentials=driver)
    completedrides=riderequest.objects.filter(trip__usercredentials=driver,status="DROPPED",rating__isnull=False)

    allratings=[]
    for rides in completedrides:
        allratings.append(rides.rating)
    
    avgrating=sum(allratings)/len(allratings)
    print("AVG :",avgrating)
    driverdetails.averagerating=avgrating
    driverdetails.save()


def ratetheride(request,currentpayment,paymentid):
    currentrequest=currentpayment.requestdetails
    currentrating=request.POST.get("rating")
    print("Rating: ",currentrating)

    currentrequest.rating=currentrating
    currentrequest.save()
    averagerating(currentrequest)
    return redirect("testpay",paymentid=paymentid)

def verifypayment(request):
    if request.method=="POST":
        data=json.loads(request.body)
        try:
            razorpayclient.utility.verify_payment_signature({
                'razorpay_order_id':data['razorpay_order_id'],
                'razorpay_payment_id':data['razorpay_payment_id'],
                'razorpay_signature':data['razorpay_signature']
            })

            currentpayment=payment.objects.get(orderid=data['razorpay_order_id'])
            currentpayment.paymentid=data['razorpay_payment_id']
            currentpayment.status="PAID"
            currentpayment.save()
            return JsonResponse({"status": "success"})
        except:
            return JsonResponse({"status": "failed"})

def createpayment(request):
    requestid=request.POST.get("requestid")
    currentrequest=riderequest.objects.get(id=requestid)

    print("RAZORID",RAZORID)
    print("RAZORSECRET",RAZORSECRET)
    razorpayclient=razorpay.Client(auth=(RAZORID,RAZORSECRET))
    amount=1000  #amount should be in paise: 10 rupees=1000 paise
    currentorder=razorpayclient.order.create({
        "amount":amount,
        "currency":"INR",
        "payment_capture": 1
    })
    print("Payment Created Successfully")
    return currentorder["id"],amount

def testpayfunction(request,paymentid):
    currentorderid=None
    currentamount=None

    currentpayment=payment.objects.get(id=paymentid)
    if request.method=="POST":
        action=request.POST.get("action")
        if action=="completepayment":
            currentorderid,currentamount=createpayment(request)
            currentpayment.orderid=currentorderid
            currentpayment.save()

        elif action=="rateride":
            return ratetheride(request,currentpayment,paymentid)


            
    return render(request, "testpay.html",{"paymentdetails":currentpayment,"orderid":currentorderid,"amount":currentamount,
                                           "RAZORID":RAZORID})





#------------------------------------------------------LANDING PAGE FUNCTIONS------------------------------------------------------
#checks if there are any pending payments
def paymentchecker(request):
    pendingpayments=payment.objects.filter(requestdetails__rider=request.user,status="PENDING")
    if pendingpayments.exists():
        pendingpayments=pendingpayments.first()
        print(f"Payment Pending for: ",pendingpayments.requestdetails)
        return pendingpayments
    return None

# Main Landing Page View
def landingfunction(request):
    user=None
    username=None
    firstname=None
    pendingpayment=None
    try:
        print("Current User Email: ", request.user.email)
        if request.user.email!=None:
            user=request.user
            status="true"
            username=User.objects.get(email=request.user.email)
            username=str(username.first_name).upper()
            username=username.split()
            firstname=username[0]

            pendingpayment=paymentchecker(request)
    except:
        print("User is not Logged in or Logged Out")
        status="false"

    if request.method=="POST":
        action=request.POST.get("action")
        if action=="paypending":
            paymentid=request.POST.get("paymentid")
            return redirect("testpay",paymentid=paymentid)
    

    
    return render(request, "landing.html", {"status":status,"user":user,"firstname":firstname,"pending":pendingpayment})

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
    requestid=request.GET.get("requestid")
    currentrequest=riderequest.objects.get(id=requestid)
    if currentrequest.status=="DROPPED" or currentride.status=="COMPLETED":
        return JsonResponse({
            "status": "COMPLETED",
            "message": "This Ride has been Ended"
        })
    
    print("Tracked Latitiude: ",currentride.currentlatitude)
    print("Tracked Longitude: ",currentride.currentlongitude)
    return JsonResponse({
        "lat": currentride.currentlatitude,"lng": currentride.currentlongitude,
        "route": json.dumps(currentride.routegeometry),"status": currentride.status,
    })

def fetchstatus(request,requestid):
    currentrequest=riderequest.objects.get(id=requestid)
    return JsonResponse({
        "status": currentrequest.status
    })

def confirmride(request):
    requestid=request.POST.get("requestid")
    requestid=request.POST.get("requestid")
    currentrequest=riderequest.objects.get(id=requestid)
    
    currentrequest.status="FULLCONFIRM"
    currentrequest.save()

    currentrequest.trip.has_boarded=True
    currentrequest.trip.save()

    return redirect("testtracking",rideid=request.POST.get("tripid"))

#to render tracking page
def testtrackingfunction(request,rideid):
    currentrideid=None
    currentride=get_object_or_404(trip, id=rideid, status="ONGOING")
    currentrideid=rideid
    
    currentrequest=riderequest.objects.get(trip=currentride,rider=request.user,status__in=["ACCEPTED", "HALFCONFIRM","FULLCONFIRM"])
    riderlatitude=currentrequest.pickuplatitude
    riderlongitude=currentrequest.pickuplongitude

    if request.method=="POST":
        action=request.POST.get("action")
        if action=="confirmride":
            return confirmride(request)

    return render(request, "testtracking.html",{"rideid":currentrideid,"requestid":currentrequest.id,"riderlatitude":riderlatitude,"riderlongitude":riderlongitude})

def rideend(currentride):
    if not currentride.has_boarded:
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
            payment.objects.create(requestdetails=riders,amount=10)
            payment.save()
            print(f"Payment Request Created for {riders}")
        print("Trip Ended")

#fetch location from driver
def updatelocation(request,rideid):
    try:
        print("Entered Function")
        currentride=trip.objects.get(id=rideid, usercredentials=request.user)
        if currentride.status=="COMPLETED":
            return JsonResponse({
                "status":"COMPLETED",
                "message":"Ride ended"
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
        return redirect("testdriver")
    
    currentrequest=riderequest.objects.filter(trip=ride, status="ACCEPTED")
    print("Current Req: ",currentrequest)

    if request.method=="POST":
        pickupid = request.POST.get("requestid")
        pickuprider=get_object_or_404(riderequest, id=pickupid, status="ACCEPTED")
        pickuprider.status="HALFCONFIRM"
        pickuprider.save()

    return render(request, "testlocation.html",{"rideid":rideid,"riders":currentrequest})




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
        lasttrip=trip.objects.filter(usercredentials=request.user,status="COMPLETED").first()
        activetrips=trip.objects.filter(usercredentials=request.user,status__in=["ACTIVE", "EMPTY"]).first()
        print("ACTIVE: ",activetrips)
        print("PAST: ",lasttrip)
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

        requests=riderequest.objects.filter(trip=activetrips,status="PENDING")
        accepted=riderequest.objects.filter(trip=activetrips,status="ACCEPTED")
    except Exception as e:
        print(e)

    action=request.POST.get("action")
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

    return render(request, "testdriver.html",{"requests":requests,"accepted":accepted,"lasttrip": lasttrip,"startride":startride,
                                              "activetrips":activetrips})





#------------------------------------------------------RIDER PAGE FUNCTIONS------------------------------------------------------

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
    lcutofftime=(formatedtime-timedelta(minutes=20)).time()
    ucutofftime=(formatedtime+timedelta(minutes=20)).time()

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

    latitude=request.session.get("riderlatitude")
    longitude=request.session.get("riderlongitude")
    print(latitude,",",longitude)

    riderequest.objects.create(trip=ride,rider=request.user,pickuplatitude=latitude,pickuplongitude=longitude)
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
            rides,latitude,longitude=riderdetails(request)
            

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






