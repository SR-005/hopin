from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingfunction, name="landing"),
    path("testlogin/", views.testloginfunction, name="testlogin"),  # test login
    path("testsignup/", views.testsignupfunction,name="testsignup"),  # test signup
    path("testcreatetrip/", views.testdriverfunction, name="testdriver"),

    path("login/", views.loginfunction, name="login"),
    path("signup/", views.signupfunction, name="signup"),
    path("logout/", views.logoutfunction, name="logout"),
]
