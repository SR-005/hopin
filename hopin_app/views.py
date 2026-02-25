from .forms import signupForm, loginForm, createtripForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import userdetail, trip
from django.contrib.auth import get_user_model
User = get_user_model()


# Create your views here.

# Main Landing Page View
def landingfunction(request):
    user = None
    try:
        print("Current User Email: ", request.user.email)
    except:
        print("User is not Logged in or Logged Out")

    return render(request, "landing.html", {"user": user})

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

            user = authenticate(request, username=useremail,
                                password=userpassword)
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
        print("Hello")
        # collect values from html form and validate it w.r.t signupForm
        signupform = signupForm(request.POST)
        if signupform.is_valid():
            firstname = signupform.cleaned_data["first_name"]
            lastname = signupform.cleaned_data["last_name"]
            useremail = signupform.cleaned_data["email"]
            userpassword = signupform.cleaned_data["password"]

            # create_user is a Django Built in function to create a User to User Model
            newuser = User.objects.create_user(
                email=useremail, password=userpassword)
            newuser.first_name = firstname
            newuser.last_name = lastname
            newuser.save()

            messages.success(request, "Account has been successfully created.")

        else:
            for errors in signupform.errors.items():  # returns a tuple of errors from the form
                # we use indexing to catch the exact error message from tuple
                messages.error(request, errors[1][0])
    return render(request, "signup.html")


def testloginfunction(request):
    if request.method == "POST":

        loginform = loginForm(request.POST)
        if loginform.is_valid():
            useremail = loginform.cleaned_data["email"]
            userpassword = loginform.cleaned_data["password"]
            print(useremail, userpassword)

            user = authenticate(request, username=useremail,
                                password=userpassword)
            if user is not None:
                login(request, user)
                messages.success(request, "Login Successfull!!")
                return redirect("landing")
            else:
                messages.error(request, "Invalid Credentials!!")
        else:
            print(loginform.errors)
    return render(request, "testlogin.html")


def testsignupfunction(request):
    if request.method == "POST":

        # collect values from html form and validate it w.r.t signupForm
        signupform = signupForm(request.POST)
        if signupform.is_valid():
            firstname = signupform.cleaned_data["first_name"]
            lastname = signupform.cleaned_data["last_name"]
            useremail = signupform.cleaned_data["email"]
            userpassword = signupform.cleaned_data["password"]

            # create_user is a Django Built in function to create a User to User Model
            newuser = User.objects.create_user(
                email=useremail, password=userpassword)
            newuser.first_name = firstname
            newuser.last_name = lastname
            newuser.save()

            messages.success(request, "Account has been successfully created.")

        else:
            for errors in signupform.errors.items():  # returns a tuple of errors from the form
                # we use indexing to catch the exact error message from tuple
                messages.error(request, errors[1][0])
    return render(request, "testsignup.html")


def testdriverfunction(request):
    userobject=request.user
    userasdriver=trip.objects.filter(usercredentials=userobject)

    # retrieve previous routes from their history
    availableroutes=[]
    for details in userasdriver:
        availableroutes.append(details.route)
    print(availableroutes)

    # retrieve last vehicle information
    index=len(userasdriver)-1
    if index>0:
        lasttrip=userasdriver[index]
    else:
        lasttrip=None

    if request.method=="POST":
        createtripform=createtripForm(request.POST)
        if createtripform.is_valid():
            # commit=False: saves the form content but doesnot upload it into db yet
            newtrip = createtripform.save(commit=False)
            newtrip.usercredentials=request.user

            if request.POST.get("route")=="other":
                trip.route = request.POST.get("customroute")
            else:
                trip.route = request.POST.get("route")
            newtrip.save()
        else:
            print("Form not Valid")
            print(request.POST)

    return render(request, "testdriver.html",
                  {"availableroutes": availableroutes, "lasttrip": lasttrip})

def testriderfunction(request):
    userobject = request.user
    userasdriver = trip.objects.filter(usercredentials=userobject)

    # retrieve previous routes from their history
    availableroutes = []
    for details in userasdriver:
        availableroutes.append(details.route)
    print(availableroutes)

    if request.method=="POST":
        location=request.POST.get("location")
        direction=request.POST.get("direction")
        if request.POST.get("route")=="other":
            route=request.POST.get("customroute")
        else:
            route=request.POST.get("route")

        print(location,route,direction)
    
    return render(request, "testrider.html",{"availableroutes": availableroutes})