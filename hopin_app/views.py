from .forms import signupForm, loginForm, createtripForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import json
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

def tripdetails(request):
    if request.method=="POST":
        createtripform=createtripForm(request.POST)
        if createtripform.is_valid():
            # commit=False: saves the form content but doesnot upload it into db yet
            newtrip = createtripform.save(commit=False)
            newtrip.usercredentials=request.user

            routegeometry=json.loads(request.POST.get("routegeometry"))

            newtrip.routegeometry=routegeometry
            coordinates=routegeometry["coordinates"]
            print(coordinates)
            newtrip.save()
        else:
            print("Form not Valid")
            print(request.POST)


def acceptride():
    print("ACCEPT")
    return 0

def rejectride():
    print("REJECT")
    return 0

def testdriverfunction(request):
    #fetch trips of the current user
    trips=trip.objects.filter(usercredentials=request.user)
    print(trips[0])
    # retrieve last vehicle information
    index=len(trips)-1
    if index>0:
        lasttrip=trips[index]
    else:
        lasttrip=None

    action=request.POST.get("action")
    if action=="tripdetails":
        tripdetails(request)
    elif action=="accept":
        acceptride()
    elif action=="reject":
        rejectride()

    return render(request, "testdriver.html",{"activetrip":trips,"lasttrip": lasttrip})


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

def testriderfunction(request):
    rides=None
    if request.method=="POST":
        action=request.POST.get("action")

        if action=="riderdetails":
            rides=riderdetails(request)
        elif action=="requestride":
            requestride(request)

    return render(request, "testrider.html",{"rides":rides})