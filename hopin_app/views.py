from django.shortcuts import render
from django.contrib import messages

# Create your views here.

def login(request):
    return render(request,"testlogin.html")

def signup(request):
    if request.method=="POST":
        newmail=request.POST.get("email")
        print("test email: ",newmail)

        if newmail.endswith("@student.aisat.ac.in"):
            messages.success(request,"Account can be created")
        else:
            messages.error(request,"User is Required to Sign In with College Mail ID.")
    return render(request,"testsignup.html")