from django.db import models


# Create your models here.
from django.contrib.auth.models import User
    
#User Details Table: contains details of each user
class useredetail(models.Model):
    usercredentials=models.OneToOneField(User, on_delete=models.CASCADE, related_name="userdetails")
    useraccess = models.CharField(default="allowed",max_length=20)
    
    def __str__(self):
        return self.username
    
