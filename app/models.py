from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CardEvent(models.Model):
    card_id = models.CharField(max_length=64)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return self.card_id

class CardUser(models.Model):
    card_id = models.CharField(max_length=64, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"Card: {self.card_id} for {self.user.username}"
