from ..models import userdetail,payment
from django.contrib.auth import get_user_model
import time
import random
import threading
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from ..forms import signupForm, loginForm
User=get_user_model()



#generate a random otp number
def otpgenerator():
    return str(random.randint(100000, 999999))

def send_email_async(request,subject, message, from_email, recipient_list):
    try:
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        messages.success(request, f"SMTP Error {e}")
        return redirect("verify")

# send otp to user email
def sendotptomail(request):
    user=request.user
    email=user.email
    phonenumber=request.POST.get("phone")

    otp=otpgenerator()
    request.session['otp']=otp
    request.session['otptime']=timezone.now().timestamp()
    request.session['phonenumber']=phonenumber
    request.session['otpsent']=True

    threading.Thread(target=send_email_async, args=(request,"HopIn OTP Verification",f"Your OTP is {otp}",settings.DEFAULT_FROM_EMAIL,
                        [email]),daemon=True).start()   
    time.sleep(5)
    messages.success(request, "OTP has been send to your Email")
    return redirect("verify")


def verifyotp(request):
    userotp=request.POST.get("otp")
    if timezone.now().timestamp()-request.session.get('otptime',0)>300:
        request.session['otpsent']=False
        messages.error(request, "OTP has Expired. Resend and Try Again")
        return redirect("verify")
    
    if userotp==request.session.get('otp'):
        userprofile=userdetail.objects.get(usercredentials=request.user)
        userprofile.phonenumber=request.session.get('phonenumber')
        userprofile.verificationpending=True
        userprofile.save()

        request.session['otpsent']=False
        messages.success(request, "OTP has been Successfully Verified.")
    else:
        messages.error(request, "Incorrect OTP. Try Again")
        request.session['otpsent']=False
        return redirect("verify")
    
    return redirect("landing")

def verifyfunction(request):
    otpsent=False
    if request.method=="POST":
        action=request.POST.get("action")
        if action=="sendotp":
            return sendotptomail(request)
        elif action=="verifyotp":
            return verifyotp(request)

    return render(request, "verify.html",{"otpsent": request.session.get('otpsent')})


#checks if there are any pending payments
def paymentchecker(request):
    pendingpayments=payment.objects.filter(requestdetails__rider=request.user,status="PENDING")
    if pendingpayments.exists():
        pendingpayments=pendingpayments.first()
        print(f"Payment Pending for: ",pendingpayments.requestdetails)
        return pendingpayments
    return None

# Main Landing Page View
def landingfunction(request):
    user=None
    username=None
    firstname=None
    pendingpayment=None

    try:
        print("Current User Email: ", request.user.email)
        if request.user.email!=None:

            userprofile=userdetail.objects.get(usercredentials=request.user)
            if userprofile.verificationpending==False:
                return redirect("verify")
            user=request.user
            status="true"
            username=User.objects.get(email=request.user.email)
            username=str(username.first_name).upper()
            username=username.split()
            firstname=username[0]

            pendingpayment=paymentchecker(request)
    except:
        print("User is not Logged in or Logged Out")
        status="false"

    if request.method=="POST":
        action=request.POST.get("action")
        if action=="paypending":
            paymentid=request.POST.get("paymentid")
            return redirect("testpay",paymentid=paymentid)
    

    
    return render(request, "landing.html", {"status":status,"user":user,"firstname":firstname,"pending":pendingpayment})

# Main Logout Function
def logoutfunction(request):
    logout(request)
    messages.success(request, "User Logged Out- Log back in to use the app!")
    return redirect("/")

# Main Login Page View
def loginfunction(request):
    if request.method=="POST":

        loginform=loginForm(request.POST)
        if loginform.is_valid():
            useremail=loginform.cleaned_data["email"]
            userpassword=loginform.cleaned_data["password"]
            print(useremail, userpassword)

            user=authenticate(request, username=useremail,password=userpassword)
            if user is not None:
                login(request, user)
                messages.success(request, "Login Successfull!!")
                return redirect("landing")
            else:
                messages.error(request, "Invalid Credentials!!")
        else:
            print(loginform.errors)
    return render(request, "login.html")

# Main Sign Up Page View
def signupfunction(request):
    if request.method=="POST":
        # collect values from html form and validate it w.r.t signupForm
        signupform=signupForm(request.POST)
        if signupform.is_valid():
            firstname=signupform.cleaned_data["first_name"]
            lastname=signupform.cleaned_data["last_name"]
            useremail=signupform.cleaned_data["email"]
            userpassword=signupform.cleaned_data["password"]

            # create_user is a Django Built in function to create a User to User Model
            newuser=User.objects.create_user(email=useremail, password=userpassword)
            newuser.first_name=firstname
            newuser.last_name=lastname
            newuser.save()
            messages.success(request, "Account has been successfully created.")

            user=authenticate(request, username=useremail,password=userpassword)
            login(request, user)
            return redirect("landing")

        else:
            for errors in signupform.errors.items():  # returns a tuple of errors from the form
                # we use indexing to catch the exact error message from tuple
                messages.error(request, errors[1][0])
    return render(request, "signup.html")
