from django.urls import path
from . import views
from .views import authview,payandrateview

urlpatterns=[
    path("testcreatetrip/", views.testdriverfunction, name="testdriver"),   #test driver
    path("testrider/", views.testriderfunction, name="testrider"),   #test rider
    path("testlocation/<int:rideid>/", views.testlocationfunction, name="testlocation"),   #test live location
    path("testtracking/<int:rideid>/", views.testtrackingfunction, name="testtracking"),   #test tracking
    path("testpay/<int:paymentid>/", payandrateview.testpayfunction, name="testpay"),

    #auth view function- LANDING PAGE
    path("", authview.landingfunction, name="landing"),
    path("login/", authview.loginfunction, name="login"),
    path("signup/", authview.signupfunction, name="signup"),
    path("verify/", authview.verifyfunction, name="verify"),
    path("logout/", authview.logoutfunction, name="logout"),


    path("rider/", views.riderfunction, name="rider"),
    
    path("updatelocation/<int:rideid>/", views.updatelocation, name="update_location"),
    path("fetchtracking/<int:rideid>/", views.fetchtracking, name="fetchtracking"),   #test tracking
    path("fetchstatus/<int:requestid>/", views.fetchstatus, name="fetchstatus"),    #fetch status of ride: completed or not
    path("verifypayment/", payandrateview.verifypayment, name="verifypayment"),
]
