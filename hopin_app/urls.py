from django.urls import path
from .views import authview,payandrateview,driverview,riderview,trackingview,locationview,profileview,testdriverview,commonview

urlpatterns=[
    #Profile view functions
    path("testprofile/", profileview.testprofilefunction, name="profile"),

    #authentication view functions
    path("", authview.landingfunction, name="landing"),
    path("login/", authview.loginfunction, name="login"),
    path("signup/", authview.signupfunction, name="signup"),
    path("verify/", authview.verifyfunction, name="verify"),
    path("logout/", authview.logoutfunction, name="logout"),

    #notification view functions
    path("register_webpush_subscription/", commonview.register_webpush_subscription, name="register_webpush_subscription"),
    path("push-debug/", commonview.push_debug_page, name="push_debug"),
    path("push-debug/status/", commonview.push_debug_status, name="push_debug_status"),

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
    # 1. The URL to load the Live Dashboard
    path('live-ride/<int:rideid>/', locationview.testlocationfunction, name='testlocation'),
    
    # 2. The background URL the map uses to update coordinates silently
    path('updatelocation/<int:rideid>/', locationview.updatelocation, name='updatelocation'),

    
]
