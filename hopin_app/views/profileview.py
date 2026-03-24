from ..models import userdetail, riderequest, payment
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import os
import json
import razorpay
from django.http import JsonResponse
from django.shortcuts import render, redirect
User=get_user_model()

def testprofilefunction(request):
    context = {
        "driver": {
            "total_rides": 12,
            "total_seats": 30,
            "reliability": 4.7,
            "active_rides": 1,
        },
        "rider": {
            "total_rides": 18,
            "pending_payments": 1,
            "completed_payments": 17,
            "ongoing": True,
        }
    }
    return render(request, "testprofile.html", context)