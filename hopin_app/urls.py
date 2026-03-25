from django.urls import path
from . import views
from .views import authview,payandrateview,driverview,riderview,trackingview,locationview,profileview,testdriverview

urlpatterns=[
    #Profile view functions
    path("testprofile/", profileview.testprofilefunction, name="profile"),

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
    path("testcreatetrip/", testdriverview.testdriverfunction, name="testdriver"),
    path("driver/", driverview.driverfunction, name="driver"),   #test driver
    #path("driver/", driverview.driverfunction, name="driver"),   #driver
    path("driver/poll/", driverview.driverpoll, name="driverpoll"),


    #rider view functions
    #path("testrider/", riderview.testriderfunction, name="testrider"),   #test rider
    path("rider/", riderview.riderfunction, name="rider"),
    path("rider/poll/", riderview.riderpoll, name="riderpoll"),


    #live location view functions
    path("testlocation/<int:rideid>/", locationview.testlocationfunction, name="testlocation"),   #test live location
    path("updatelocation/<int:rideid>/", locationview.updatelocation, name="update_location"),
    
    #location tracking view functions
    path("testtracking/<int:rideid>/", trackingview.testtrackingfunction, name="testtracking"),   #test tracking
    path("fetchtracking/<int:rideid>/", trackingview.fetchtracking, name="fetchtracking"),   #test tracking
    path("fetchstatus/<int:requestid>/", trackingview.fetchstatus, name="fetchstatus"),    #fetch status of ride: completed or not
    path("tracking/<int:rideid>/", trackingview.trackingfunction, name="tracking"),   #test tracking

    
]
