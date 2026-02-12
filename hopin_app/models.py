from django.db import models

# Create your models here.

#creating admin model
from django.contrib.auth.models import BaseUserManager
class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


#creating custom User Model usin AbstractUser Model
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    username=None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # no username required

    objects = UserManager() 

    def __str__(self):
        return self.email
    
#User Details Table: contains details of each user
class userdetail(models.Model):
    id=models.AutoField(primary_key=True)
    usercredentials=models.OneToOneField(User, on_delete=models.CASCADE, related_name="userdetails")
    paymentpending = models.BooleanField(default="False")
    
    def __str__(self):
        return self.usercredentials.email
    
class driverdetail(models.Model):
    id=models.AutoField(primary_key=True)
    usercredentials=models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver")
    preferedlocation=models.CharField()                 #location suggession
    prefereddirection=models.CharField()                #direction suggession
    vehiclenumber=models.CharField(max_length=12)       #KL 41 **** ****
    vehicletype=models.CharField()                      #car or bike
    vehiclemodel=models.CharField()                     #car or bike model name