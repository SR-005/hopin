from django.shortcuts import render
from .forms import signupForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.

def login(request):
    return render(request,"testlogin.html")

def signup(request):
    if request.method=="POST":

        signupform=signupForm(request.POST)             #collect values from html form and validate it w.r.t signupForm
        if signupform.is_valid():
            username=signupform.cleaned_data["username"]
            useremail=signupform.cleaned_data["email"]
            userpassword=signupform.cleaned_data["password"]

            '''print("Name: ",username)
            print("Email: ",useremail)
            print("Password: ",userpassword)'''

            #create_user is a Django Built in function to create a User to User Model
            newuser=User.objects.create_user(username=username,email=useremail,password=userpassword)  

            messages.success(request,"Account has been successfully created.")

        else:
            for errors in signupform.errors.items():        #returns a tuple of errors from the form
                messages.error(request,errors[1][0])            #we use indexing to catch the exact error message from tuple
    return render(request,"testsignup.html")