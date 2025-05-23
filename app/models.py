from django.db import models

# Create your models here.

class CardEvent(models.Model):
    card_id = models.CharField(max_length=64)
    timestamp = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
