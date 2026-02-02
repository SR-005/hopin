from django import forms
from .models import user

class signupForm(forms.ModelForm):
    class Meta:
        model=user              #model name
        fields=["username","useremail","userpassword"]      #field names of db that come from form