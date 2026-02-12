from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import userdetail

User = get_user_model()

#function to auto update userdetail when a new user is created
@receiver(post_save, sender=User)
def create_user_detail(sender, instance, created, **kwargs):
    if created:
        userdetail.objects.create(usercredentials=instance)
