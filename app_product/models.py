from django.db import models
from django.contrib.auth.models import User
from app_reference.models import Shop, Supplier, Product, ProductCategory

# import datetime
from datetime import datetime, date
from django.utils import timezone
# import pytz


# Create your models here. 

class Document (models.Model):
    title = models.CharField(max_length=50)
    # datetime = models.DateTimeField(default=datetime.today())
    datetime = models.DateTimeField(default=timezone.now, blank=True)
    # datetime = models.DateTimeField(default=timezone.now(), blank=True)
    # datetime = models.DateField(default=date.today())
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    

    def __int__(self):
        return self.id


class Delivery (models.Model):
    # date = models.DateTimeField(default=datetime.now(), blank=True)
    # date = models.DateTimeField(default=timezone.now(), blank=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)#counter
    quantity_plus = models.IntegerField(default=0)
    # quantity_minus = models.IntegerField(default=0) 
    # quantity_remainder = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'delivery'
        verbose_name_plural = 'deliveries'

    def __int__(self):
        return self.id

class Sale (models.Model):
    # date = models.DateTimeField(default=datetime.now(), blank=True)
    # date = models.DateTimeField(default=timezone.now(), blank=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)#counter
    # quantity_plus = models.IntegerField(default=0)
    quantity_minus = models.IntegerField(default=0) 
    # quantity_remainder = models.IntegerField(default=0)


    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'sale'
        verbose_name_plural = 'sales'

    def __int__(self):
        return self.id


class Transfer (models.Model):
    # date = models.DateTimeField(default=datetime.now(), blank=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    sender_shop = models.ForeignKey(Shop, related_name='sender_shop', on_delete=models.DO_NOTHING)
    receiver_shop = models.ForeignKey(Shop, related_name='receiver_shop', on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)#counter
    quantity = models.IntegerField(default=0) 
    


    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'transfer'
        verbose_name_plural = 'transfers'

    def __int__(self):
        return self.id

class Remainder (models.Model):
    # date = models.DateTimeField(default=datetime.now(), blank=True)
    # date = models.DateTimeField(default=timezone.now(), blank=True)
    # document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    # price = models.IntegerField(default=0)
    # quantity_plus = models.IntegerField(default=0)
    # quantity_minus = models.IntegerField(default=0) 
    quantity_remainder = models.IntegerField(default=0)


    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'remainder'
        verbose_name_plural = 'remainders'

    def __int__(self):
        return self.id

        