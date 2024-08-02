from django.db import models
from django.contrib.auth.models import User
from app_reference.models import ProductCategory
# import datetime
from datetime import datetime, date
from django.utils import timezone

# Create your models here.

class BonusAccount (models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    smarts=models.IntegerField(default=0)
    phones=models.IntegerField(default=0)
    acces=models.IntegerField(default=0)
    sims=models.IntegerField(default=0)
    modems=models.IntegerField(default=0)
    insurance=models.IntegerField(default=0)
    esset=models.IntegerField(default=0)
    wink=models.IntegerField(default=0)
    service=models.IntegerField(default=0)
    other=models.IntegerField(default=0)
    
    def __int__(self):
        return self.id

class Salary (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    paid=models.IntegerField(default=0)

    def __int__(self):
        return self.id


class BulkSimMotivation (models.Model):
    sim_price=models.IntegerField(default=0)
    bonus_per_sim=models.IntegerField(default=0)

    def __int__(self):
        return self.id
