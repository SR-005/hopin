from django import forms
from .models import user

class signupForm(forms.ModelForm):
    userpassword=forms.CharField(widget=forms.PasswordInput())      #widget=forms.PasswordInput(): it is used to prevent password exposing through form 
    class Meta:
        model=user              #model name
        fields=["username","useremail"]      #field names of db that come from form(htmlid=model field name)