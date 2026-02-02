from django.shortcuts import render
from .forms import signupForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.

def login(request):
    return render(request,"testlogin.html")

def signup(request):
    if request.method=="POST":
        signupform=signupForm(request.POST)             #collect values from html form and validate it w.r.t signupForm
        if signupform.is_valid():
            username=signupform.cleaned_data["username"]
            useremail=signupform.cleaned_data["useremail"]
            userpassword=signupform.cleaned_data["userpassword"]

            hashedpassword=make_password(userpassword)
            print(check_password(userpassword,hashedpassword))

            print("Name: ",username)
            print("Email: ",useremail)
            print("Password: ",userpassword)
            print("Hashed Password: ",hashedpassword)

            messages.success(request,"Account can be created")
        else:
            for errors in signupform.errors.items():        #returns a tuple of errors from the form
                messages.error(request,errors[1][0])            #we use indexing to catch the exact error message from tuple
    return render(request,"testsignup.html")