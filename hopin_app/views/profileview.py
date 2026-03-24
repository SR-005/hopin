from ..models import userdetail, riderequest, payment,trip
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import os
import json
import razorpay
from django.http import JsonResponse
from django.shortcuts import render, redirect
User=get_user_model()

def testprofilefunction(request):
    user=request.user
    completedtrips=trip.objects.filter(usercredentials=user,status="COMPLETED")
    counttrips=len(completedtrips)
    droppedrides=riderequest.objects.filter(rider=user,status="DROPPED")
    countrides=len(droppedrides)
    return render(request, "testprofile.html", {"completedtrips":completedtrips,"droppedrides":droppedrides,"counttrips":counttrips,
                                                "countrides":countrides})