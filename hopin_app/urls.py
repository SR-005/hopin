from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingfunction, name="landing"),
    path("testlogin/", views.testloginfunction, name="testlogin"),
    path("login/", views.loginfunction, name="login"),
    path("logout/", views.logoutfunction, name="logout"),
    path("testsignup/", views.testsignupfunction, name="testsignup"),
    path("testcreateride/", views.testdriverfunction, name="testdriver"),
]
