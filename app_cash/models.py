from django.db import models
from django.contrib.auth.models import User
from app_reference.models import Shop
from app_product.models import Document
# import datetime
from datetime import datetime, date
from django.utils import timezone

# Create your models here.

class Cash (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    pre_remainder= models.IntegerField(default=0)
    cash_in= models.IntegerField(default=0)
    cash_out= models.IntegerField(default=0)
    current_remainder= models.IntegerField(default=0)

    def __int__(self):
        return self.id

#model used to store current cash remainder at shop
class CashRemainder(models.Model):
    remainder=models.IntegerField(default=0)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    
    def __int__(self):
        return self.remainder
   

class Credit (models.Model):
    created = models.DateField(auto_now_add=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    sum= models.IntegerField(default=0)

    def __int__(self):
        return self.id

class Card (models.Model):
    created = models.DateField(auto_now_add=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    sum= models.IntegerField(default=0)

    def __int__(self):
        return self.id