from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingfunction, name="landing"),
    path("testcreatetrip/", views.testdriverfunction, name="testdriver"),   #test driver
    path("testrider/", views.testriderfunction, name="testrider"),   #test rider
    path("testlocation/", views.testlocationfunction, name="testlocation"),   #test rider

    path("login/", views.loginfunction, name="login"),
    path("signup/", views.signupfunction, name="signup"),
    path("logout/", views.logoutfunction, name="logout"),
]
