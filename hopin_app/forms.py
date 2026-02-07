from django import forms
from .models import User
from django.core.exceptions import ValidationError

class signupForm(forms.ModelForm):
    password=forms.CharField(widget=forms.PasswordInput())      #widget=forms.PasswordInput(): it is used to prevent password exposing through form


    class Meta:
        model=User              #model name
        fields=["username","email"]      #field names of db that come from form(htmlid=model field name)


    def clean_email(self):
        email=self.cleaned_data["email"]
        if not email.endswith("@student.aisat.ac.in"):
            raise ValidationError("Only college email addresses (@student.aisat.ac.in) are allowed.")
        return email