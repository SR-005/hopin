from django.shortcuts import render
from django.contrib import messages

# Create your views here.

def login(request):
    return render(request,"testlogin.html")

def signup(request):
    return render(request,"signup.html")