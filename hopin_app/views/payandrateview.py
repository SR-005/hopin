from ..models import userdetail, riderequest, payment
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
import os
import json
import razorpay
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from ..notifications import send_payment_received_notification, send_payment_success_notification
User=get_user_model()


load_dotenv()
RAZORID=os.getenv("RAZORPAYKEY")
RAZORSECRET=os.getenv("RAZORPAYSECRET")
razorpayclient=razorpay.Client(auth=(RAZORID, RAZORSECRET))

def averagerating(currentrequest):
    driver=currentrequest.trip.usercredentials
    driverdetails, _ = userdetail.objects.get_or_create(usercredentials=driver)
    avgrating = riderequest.objects.filter(
        trip__usercredentials=driver,
        status="DROPPED",
        rating__isnull=False
    ).aggregate(avg_rating=Avg("rating"))["avg_rating"]

    print("AVG :", avgrating)
    driverdetails.averagerating=round(avgrating,1) if avgrating is not None else None
    driverdetails.save()


def ratetheride(request, currentpayment, paymentid):
    currentrequest=currentpayment.requestdetails
    currentrating = request.POST.get("rating")
    print("Rating: ", currentrating)

    try:
        currentrating = int(currentrating)
    except (TypeError, ValueError):
        return redirect("testpay", paymentid=paymentid)

    if currentrating < 1 or currentrating > 5:
        return redirect("testpay", paymentid=paymentid)

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
            send_payment_success_notification(currentpayment.requestdetails.rider, currentpayment.amount)
            send_payment_received_notification(
                currentpayment.requestdetails.trip.usercredentials,
                currentpayment.requestdetails.rider,
                currentpayment.amount,
            )
            return JsonResponse({"status": "success"})
        except:
            return JsonResponse({"status": "failed"})


def createpayment(request):
    requestid=request.POST.get("requestid")
    currentrequest=get_object_or_404(riderequest, id=requestid)
    paymentrecord=get_object_or_404(payment, requestdetails=currentrequest)

    print("RAZORID", RAZORID)
    print("RAZORSECRET", RAZORSECRET)
    razorpayclient=razorpay.Client(auth=(RAZORID, RAZORSECRET))
    amount_rupees = float(paymentrecord.amount or 0)
    amount=max(100, int(round(amount_rupees * 100)))  # Razorpay expects paise and enforces a minimum amount
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
