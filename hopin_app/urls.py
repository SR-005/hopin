from django.urls import path
from . import views
from .views import authview,payandrateview,driverview,riderview,trackingview,locationview

urlpatterns=[

    #authentication view functions
    path("", authview.landingfunction, name="landing"),
    path("login/", authview.loginfunction, name="login"),
    path("signup/", authview.signupfunction, name="signup"),
    path("verify/", authview.verifyfunction, name="verify"),
    path("logout/", authview.logoutfunction, name="logout"),


    #payment and rating view functions
    path("testpay/<int:paymentid>/", payandrateview.testpayfunction, name="testpay"),
    path("verifypayment/", payandrateview.verifypayment, name="verifypayment"),


    #driver view functions
    path("testcreatetrip/", driverview.testdriverfunction, name="testdriver"),   #test driver


    #rider view functions
    #path("testrider/", riderview.testriderfunction, name="testrider"),   #test rider
    path("rider/", riderview.riderfunction, name="rider"),


    #live location view functions
    path("testlocation/<int:rideid>/", locationview.testlocationfunction, name="testlocation"),   #test live location
    path("updatelocation/<int:rideid>/", locationview.updatelocation, name="update_location"),
    
    #location tracking view functions
    path("testtracking/<int:rideid>/", trackingview.testtrackingfunction, name="testtracking"),   #test tracking
    path("fetchtracking/<int:rideid>/", trackingview.fetchtracking, name="fetchtracking"),   #test tracking
    path("fetchstatus/<int:requestid>/", trackingview.fetchstatus, name="fetchstatus"),    #fetch status of ride: completed or not
    
]
