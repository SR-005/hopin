from ..models import userdetail, trip, riderequest, payment
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import os
import json
import razorpay
from django.http import JsonResponse
from django.contrib import messages
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
    driverdetails.averagerating=avgrating
    driverdetails.save()


def ratetheride(request, currentpayment, paymentid):
    currentrequest=currentpayment.requestdetails
    currentrating=request.POST.get("rating")
    print("Rating: ", currentrating)

    currentrequest.rating=currentrating
    currentrequest.save()
    averagerating(currentrequest)
    return redirect("testpay", paymentid=paymentid)


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
    requestid=request.POST.get("requestid")
    currentrequest=riderequest.objects.get(id=requestid)

    print("RAZORID", RAZORID)
    print("RAZORSECRET", RAZORSECRET)
    razorpayclient=razorpay.Client(auth=(RAZORID, RAZORSECRET))
    amount=1000  # amount should be in paise: 10 rupees=1000 paise
    currentorder=razorpayclient.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    print("Payment Created Successfully")
    return currentorder["id"], amount


def testpayfunction(request, paymentid):
    currentorderid=None
    currentamount=None

    currentpayment=payment.objects.get(id=paymentid)
    if request.method == "POST":
        action=request.POST.get("action")
        if action == "completepayment":
            currentorderid, currentamount=createpayment(request)
            currentpayment.orderid=currentorderid
            currentpayment.save()

        elif action == "rateride":
            return ratetheride(request, currentpayment, paymentid)

    return render(request, "testpay.html", {"paymentdetails": currentpayment, "orderid": currentorderid, "amount": currentamount,
                                           "RAZORID": RAZORID})