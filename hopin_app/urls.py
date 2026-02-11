from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingfunction, name="landing"),
    path("testlogin/", views.testloginfunction, name="testlogin"),
    path("login/", views.loginfunction, name="login"),
    path("testsignup/", views.signupfunction, name="testsignup"),
    path("createride/", views.driverfunction, name="testdriver"),
]
