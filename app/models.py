from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CardEvent(models.Model):
    card_id = models.CharField(max_length=64)
    # timestamp = models.CharField(max_length=64) # Removed to avoid NOT NULL constraint issue and redundancy with created_at
    created_at = models.DateTimeField(auto_now_add=True)
    # user_name = models.CharField(max_length=64) # Removed as it's looked up from CardUser
    def __str__(self):
        return self.card_id

class CardUser(models.Model):
    card_id = models.CharField(max_length=64, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"Card: {self.card_id} for {self.user.username}"
