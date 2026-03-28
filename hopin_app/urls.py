from django.urls import path
from .views import authview,payandrateview,driverview,riderview,trackingview,locationview,profileview,testdriverview,commonview
from webpush.views import ServiceWorkerView, save_info

urlpatterns=[
    #web push routes
    path("save_information", save_info, name="save_webpush_info"),
    path("service-worker.js", ServiceWorkerView.as_view(), name="service_worker"),

    #Profile view functions
    path("testprofile/", profileview.testprofilefunction, name="profile"),

    #authentication view functions
    path("", authview.landingfunction, name="landing"),
    path("login/", authview.loginfunction, name="login"),
    path("signup/", authview.signupfunction, name="signup"),
    path("verify/", authview.verifyfunction, name="verify"),
    path("logout/", authview.logoutfunction, name="logout"),

    #payment and rating view functions
    path("verifypayment/", payandrateview.verifypayment, name="verifypayment"),


    #driver view functions
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
    path("fetchtracking/<int:rideid>/", trackingview.fetchtracking, name="fetchtracking"),   #test tracking
    path("fetchstatus/<int:requestid>/", trackingview.fetchstatus, name="fetchstatus"),    #fetch status of ride: completed or not
    path("tracking/<int:rideid>/", trackingview.trackingfunction, name="tracking"),   #test tracking
    # 1. The URL to load the Live Dashboard
    path('live-ride/<int:rideid>/', locationview.testlocationfunction, name='testlocation'),
    
    # 2. The background URL the map uses to update coordinates silently
    path('updatelocation/<int:rideid>/', locationview.updatelocation, name='updatelocation'),

    
]
