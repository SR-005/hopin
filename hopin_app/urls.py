from django.urls import path
from . import views

urlpatterns=[
    path("testcreatetrip/", views.testdriverfunction, name="testdriver"),   #test driver
    path("testrider/", views.testriderfunction, name="testrider"),   #test rider
    path("testlocation/<int:rideid>/", views.testlocationfunction, name="testlocation"),   #test live location
    path("testtracking/<int:rideid>/", views.testtrackingfunction, name="testtracking"),   #test tracking
    path("testpay/<int:paymentid>/", views.testpayfunction, name="testpay"),

    path("", views.landingfunction, name="landing"),
    path("login/", views.loginfunction, name="login"),
    path("signup/", views.signupfunction, name="signup"),
    path("verify/", views.verifyfunction, name="verify"),
    path("logout/", views.logoutfunction, name="logout"),
    path("rider/", views.riderfunction, name="rider"),
    
    path("updatelocation/<int:rideid>/", views.updatelocation, name="update_location"),
    path("fetchtracking/<int:rideid>/", views.fetchtracking, name="fetchtracking"),   #test tracking
    path("fetchstatus/<int:requestid>/", views.fetchstatus, name="fetchstatus"),    #fetch status of ride: completed or not
    path("verifypayment/", views.verifypayment, name="verifypayment"),
]
