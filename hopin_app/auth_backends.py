from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username, password, **kwargs):
        try:
            user=User.objects.get(email=username)       #gets user object using email: here username is prompted email by user
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and user.is_active:        #checked if password is correct and user is currently is active
            return user
        
        return None

