from django.db import models
from django.core.exceptions import ValidationError

#validation functions
def verifyemail(email):
    if not email.endswith("@student.aisat.ac.in"):
        raise ValidationError("Only @aisat.ac.in email addresses are allowed.")
    return 0



# Create your models here.
class user(models.Model):
    userid=models.AutoField(primary_key=True)
    username=models.CharField(max_length=100)
    useremail=models.EmailField(unique=True, validators=[verifyemail])
    userpassword=models.CharField(max_length=50)
    useraccess=models.CharField(default="allowed")

    def __str__(self):
        return self.username