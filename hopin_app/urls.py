from django.urls import path
from . import views

urlpatterns = [
    path("", views.landingfunction, name="landing"),
    path("login/", views.loginfunction, name="testlogin"),
    path("signup/", views.signupfunction, name="testsignup"),
]