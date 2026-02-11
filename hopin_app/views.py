from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login

from .forms import signupForm,loginForm

# Create your views here.

def landingfunction(request):
    user=None
    return render(request,"landing.html",{"user":user})

def loginfunction(request):
    if request.method=="POST":
        
        loginform=loginForm(request.POST)
        if loginform.is_valid():
            useremail=loginform.cleaned_data["email"]
            userpassword=loginform.cleaned_data["password"]
            print(useremail, userpassword)
            
            user=authenticate(request,username=useremail,password=userpassword)
            if user is not None:
                login(request,user)
                messages.success(request,"Login Successfull!!")
                return redirect("landing")
            else:
                messages.error(request,"Invalid Credentials!!")
        else:
            print(loginform.errors)
    return render(request,"testlogin.html")

def signupfunction(request):
    if request.method=="POST":

        signupform=signupForm(request.POST)             #collect values from html form and validate it w.r.t signupForm
        if signupform.is_valid():
            firstname=signupform.cleaned_data["first_name"]
            lastname=signupform.cleaned_data["last_name"]
            useremail=signupform.cleaned_data["email"]
            userpassword=signupform.cleaned_data["password"]

            #create_user is a Django Built in function to create a User to User Model
            newuser=User.objects.create_user(email=useremail,password=userpassword)  
            newuser.first_name=firstname    
            newuser.last_name=lastname
            newuser.save()
            messages.success(request,"Account has been successfully created.")

        else:
            for errors in signupform.errors.items():        #returns a tuple of errors from the form
                messages.error(request,errors[1][0])            #we use indexing to catch the exact error message from tuple
    return render(request,"testsignup.html")

def driverfunction(request):
    return render(request,"testdriver.html")