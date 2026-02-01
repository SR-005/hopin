from django.urls import path
from . import views

urlpatterns = [
    path("", views.login, name="testlogin"),
    path("signup/", views.signup, name="testsignup"),
]