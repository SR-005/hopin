from ..models import userdetail, riderequest, payment,trip
from ..email.brevo import sendemail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib import messages
from dotenv import load_dotenv
import os
import json
import razorpay
from django.db.models import Avg, Sum
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
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
    currentrequest=get_object_or_404(riderequest, id=requestid)
    paymentrecord=get_object_or_404(payment, requestdetails=currentrequest)

    print("RAZORID", RAZORID)
    print("RAZORSECRET", RAZORSECRET)
    razorpayclient=razorpay.Client(auth=(RAZORID, RAZORSECRET))
    amount_rupees=float(paymentrecord.amount or 0)
    amount=max(100, int(round(amount_rupees * 100)))  # Razorpay expects paise and enforces a minimum amount
    currentorder=razorpayclient.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })
    print("Payment Created Successfully")
    return currentorder["id"], amount

@login_required
def testprofilefunction(request):
    user=request.user
    completedtrips=None
    droppedrides=None
    counttrips=None
    countrides=None
    currentorderid=None
    currentamount=None
    currentaverage=None

    completedtrips=trip.objects.filter(usercredentials=user,status="COMPLETED").order_by("-ridedate")
    counttrips=len(completedtrips)
    droppedrides=riderequest.objects.filter(rider=user,status="DROPPED").order_by("-trip__ridedate")
    countrides=len(droppedrides)
    userobject=userdetail.objects.get(usercredentials=user)
    currentaverage=userobject.averagerating
    phonenumber=userobject.phonenumber
    print("Phone Number: ",phonenumber)


    rider_pending_payments=payment.objects.filter(requestdetails__rider=request.user,status="PENDING").select_related(
                                    "requestdetails__rider","requestdetails__trip__usercredentials").order_by(
                                    "-requestdetails__trip__ridedate", "-id")

    driver_receivables=payment.objects.filter(requestdetails__trip__usercredentials=request.user,status="PENDING").select_related(
                                    "requestdetails__rider","requestdetails__trip").order_by(
                                    "-requestdetails__trip__ridedate", "-id")

    rider_pending_total=rider_pending_payments.aggregate(total=Sum("amount"))["total"] or 0
    driver_receivable_total=driver_receivables.aggregate(total=Sum("amount"))["total"] or 0

    if request.method=="POST":
        action=request.POST.get("action")
        if action=="paypending":
            requestid=request.POST.get("requestid")
            currentrating=request.POST.get("rating")
            currentrequest=riderequest.objects.get(id=requestid)

            if currentrequest.rating is None:
                try:
                    currentrating = int(currentrating)
                except (TypeError, ValueError):
                    return redirect("profile")

                if currentrating < 1 or currentrating > 5:
                    return redirect("profile")

                currentrequest.rating=currentrating
                currentrequest.save()
                averagerating(currentrequest)

            paymentid=request.POST.get("paymentid")
            currentpayment=payment.objects.get(id=paymentid)
            currentorderid, currentamount=createpayment(request)
            currentpayment.orderid=currentorderid
            currentpayment.save()
        elif action=="submitcomplaint":
            complaint_name = (request.POST.get("complaint_name") or user.get_full_name() or user.email).strip()
            complaint_email = (request.POST.get("complaint_email") or user.email).strip()
            complaint_message = (request.POST.get("complaint_message") or "").strip()

            if not complaint_message:
                messages.error(request, "Please describe your complaint before sending it.")
                return redirect("profile")

            email_subject = f"Hop In Complaint from {complaint_name}"
            email_body = (
                f"Name: {complaint_name}\n"
                f"Email: {complaint_email}\n\n"
                "Complaint Details:\n"
                f"{complaint_message}\n"
            )

            try:
                sendemail(email_subject, email_body, settings.DEFAULT_FROM_EMAIL)
                messages.success(request, "Complaint submitted successfully.")
            except Exception:
                messages.error(request, "Complaint could not be submitted right now. Please try again.")

            return redirect("profile")

    return render(request, "testprofile.html", {"completedtrips":completedtrips,"droppedrides":droppedrides,"counttrips":counttrips,
                                                "countrides":countrides,"averagerating":currentaverage,"phonenumber":phonenumber,
                                                "rider_pending_payments":rider_pending_payments,
                                                "driver_receivables":driver_receivables,
                                                "rider_pending_total":rider_pending_total,
                                                "driver_receivable_total":driver_receivable_total,
                                                "orderid": currentorderid, "amount": currentamount,
                                                "RAZORID": RAZORID})
