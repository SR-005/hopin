from django.db import models

# Create your models here.

#creating admin model
from django.contrib.auth.models import BaseUserManager
class UserManager(BaseUserManager):
    use_in_migrations=True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")

        email=self.normalize_email(email)
        user=self.model(email=email, **extra_fields)
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
    email=models.EmailField(unique=True)

    USERNAME_FIELD="email"
    REQUIRED_FIELDS=[]        # no username required

    objects=UserManager() 

    def __str__(self):
        return self.email
    
#User Details Table: contains details of each user
class userdetail(models.Model):
    id=models.AutoField(primary_key=True)
    usercredentials=models.OneToOneField(User, on_delete=models.CASCADE, related_name="userdetails")
    phonenumber=models.CharField(max_length=15,null=True, blank=True)
    averagerating=models.FloatField(null=True, blank=True)
    verificationpending=models.BooleanField(default="False")
    
    def __str__(self):
        return self.usercredentials.email
    
class trip(models.Model):
    id=models.AutoField(primary_key=True)
    usercredentials=models.ForeignKey(User, on_delete=models.CASCADE, related_name="driver")
    preferedlocation=models.CharField()                 #location suggession
    latitude=models.FloatField(null=False, blank=False)
    longitude=models.FloatField(null=False, blank=False)
    routegeometry=models.JSONField(null=True, blank=True)                         #route path (lat and long)
    prefereddirection=models.CharField(null=False, blank=False)                #direction suggession
    ridedate=models.DateField(null=False, blank=False)
    ridetime=models.TimeField(null=False, blank=False)
    currentlatitude=models.FloatField(null=True, blank=True)            #used for live location tracking
    currentlongitude=models.FloatField(null=True, blank=True)           #used for live location tracking
    lastlocationupdate=models.DateTimeField(null=True, blank=True)
    vehicletype=models.CharField(null=False, blank=False)                      #car or bike
    helmet=models.CharField(null=True, blank=True) 
    availableseats=models.IntegerField(null=False, blank=False)
    vehiclenumber=models.CharField(max_length=12,null=False, blank=False)       #KL 41 **** ****
    vehiclemodel=models.CharField(null=False, blank=False)                     #car or bike model name
    status=models.CharField(default="EMPTY")
    has_boarded=models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.usercredentials.email} : {self.status}"


class riderequest(models.Model):
    id=models.AutoField(primary_key=True)
    trip=models.ForeignKey(trip, on_delete=models.CASCADE, related_name="tripdetails")
    rider=models.ForeignKey(User, on_delete=models.CASCADE, related_name="riderdetails")
    pickuplatitude=models.FloatField(null=True, blank=True)
    pickuplongitude=models.FloatField(null=True, blank=True)
    rating=models.IntegerField(null=True, blank=True)
    status=models.CharField(default="PENDING")

    class Meta:
        unique_together=("trip", "rider")

    def __str__(self):
        return f"{self.rider.email} → Ride {self.trip.usercredentials} : {self.status}"
    
class payment(models.Model):
    id=models.AutoField(primary_key=True)
    requestdetails=models.OneToOneField(riderequest,on_delete=models.CASCADE, related_name="paymentdetails")
    amount=models.FloatField()
    status=models.CharField(default="PENDING")
    orderid=models.CharField(null=True,blank=True)
    paymentid=models.CharField(null=True,blank=True)

    def __str__(self):
        return f"{self.requestdetails} : {self.status}"