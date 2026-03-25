from ..models import userdetail, riderequest, payment,trip
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import os
import json
import razorpay
from django.http import JsonResponse
from django.shortcuts import render, redirect
User=get_user_model()

load_dotenv()
RAZORID=os.getenv("RAZORPAYKEY")
RAZORSECRET=os.getenv("RAZORPAYSECRET")
razorpayclient=razorpay.Client(auth=(RAZORID, RAZORSECRET))


def averagerating(currentrequest):
    driver=currentrequest.trip.usercredentials
    driverdetails=userdetail.objects.get(usercredentials=driver)
    completedrides=riderequest.objects.filter(trip__usercredentials=driver, status="DROPPED", rating__isnull=False)

    allratings=[]
    for rides in completedrides:
        allratings.append(rides.rating)

    avgrating=sum(allratings)/len(allratings)
    print("AVG :", avgrating)
    driverdetails.averagerating=round(avgrating,1)
    driverdetails.save()

def verifypayment(request):
    if request.method == "POST":
        data=json.loads(request.body)
        try:
            razorpayclient.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })

            currentpayment=payment.objects.get(
                orderid=data['razorpay_order_id'])
            currentpayment.paymentid=data['razorpay_payment_id']
            currentpayment.status="PAID"
            currentpayment.save()
            return JsonResponse({"status": "success"})
        except:
            return JsonResponse({"status": "failed"})


def createpayment(request):
    print("ENTER CREATE PAYMENT")
    requestid=request.POST.get("requestid")
    currentrequest=riderequest.objects.get(id=requestid)
    paymentrecord=payment.objects.get(requestdetails=currentrequest)

    print("RAZORID", RAZORID)
    print("RAZORSECRET", RAZORSECRET)
    razorpayclient=razorpay.Client(auth=(RAZORID, RAZORSECRET))
    amount_rupees=paymentrecord.amount
    amount=max(100, int(round(amount_rupees * 100)))  # Razorpay expects paise and enforces a minimum amount
    currentorder=razorpayclient.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    print("Payment Created Successfully")
    return currentorder["id"], amount

def testprofilefunction(request):
    user=request.user
    completedtrips=None
    droppedrides=None
    counttrips=None
    countrides=None
    currentorderid=None
    currentamount=None

    '''completedtrips=trip.objects.filter(usercredentials=user,status="COMPLETED")
    counttrips=len(completedtrips)
    droppedrides=riderequest.objects.filter(rider=user,status="DROPPED")
    countrides=len(droppedrides)'''

    pendingpayments=payment.objects.filter(requestdetails__rider=request.user,status="PENDING")
    if pendingpayments.exists():
        pendingpayments=pendingpayments.first() 

    if request.method=="POST":
        action=request.POST.get("action")
        if action=="paypending":
            requestid=request.POST.get("requestid")
            currentrating=request.POST.get("rating")
            currentrequest=riderequest.objects.get(id=requestid)

            currentrequest.rating=currentrating
            currentrequest.save()
            averagerating(currentrequest)

            paymentid=request.POST.get("paymentid")
            currentpayment=payment.objects.get(id=paymentid)
            currentorderid, currentamount=createpayment(request)
            currentpayment.orderid=currentorderid
            currentpayment.save()

    return render(request, "testprofile.html", {"completedtrips":completedtrips,"droppedrides":droppedrides,"counttrips":counttrips,
                                                "countrides":countrides,"pendingpayments":pendingpayments, "orderid": currentorderid, "amount": currentamount,
                                                "RAZORID": RAZORID})