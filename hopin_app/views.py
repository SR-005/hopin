from django.shortcuts import render
from .forms import signupForm
from django.contrib import messages

# Create your views here.

def login(request):
    return render(request,"testlogin.html")

def signup(request):
    if request.method=="POST":
        signupform=signupForm(request.POST)             #collect values from html form and validate it w.r.t signupForm
        if signupform.is_valid():
            username=request.POST.get("username")
            useremail=request.POST.get("useremail")
            userpassword=request.POST.get("userpassword")
            
            print("Name: ",username)
            print("Email: ",useremail)
            print("Password: ",userpassword)

            messages.success(request,"Account can be created")
        else:
            for errors in signupform.errors.items():        #returns a tuple of errors from the form
                messages.error(request,errors[1][0])            #we use indexing to catch the exact error message from tuple
    return render(request,"testsignup.html")