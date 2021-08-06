from django.db import models
from django.contrib.auth.models import User
from django.db.models import manager
from app_reference.models import Shop, Supplier, Product, ProductCategory, DocumentType

# import datetime
from datetime import datetime, date
from django.utils import timezone


# import pytz


# Create your models here. 

class Document (models.Model):
    title = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    sum = models.IntegerField(null=True)
    
    def __int__(self):
        return self.id

    # class Meta:
    #     ordering = ('created',)  # sorting by date
    #     verbose_name = self.title
    

class Identifier(models.Model):
    def __int__(self):
        return self.id


class Delivery (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, related_name='delivery')
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)#counter
    quantity = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'delivery'
        verbose_name_plural = 'deliveries'

    # def sub_total(self):
    #     return self.price * self.quantity

    def __int__(self):
        return self.id

class Sale (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    category = models.ForeignKey(ProductCategory, null=True, on_delete=models.DO_NOTHING)
    date = models.DateTimeField(default=timezone.now, blank=True)
    identifier = models.ForeignKey(Identifier, null=True, blank=True,on_delete=models.DO_NOTHING)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.DO_NOTHING)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    quantity = models.IntegerField(default=0)
    sub_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    staff_bonus= models.IntegerField(default=0)
    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'sale'
        verbose_name_plural = 'sales'

    # def sub_total(self):
    #     return int(self.price) * int(self.quantity)

    def __int__(self):
        return self.id


class Transfer (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop_sender = models.ForeignKey(Shop, related_name='sender_shop', on_delete=models.DO_NOTHING)
    shop_receiver = models.ForeignKey(Shop, related_name='receiver_shop', on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)#counter
    quantity = models.IntegerField(default=0) 
    sub_total = models.IntegerField(default=0) 
    


    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'transfer'
        verbose_name_plural = 'transfers'

    def __int__(self):
        return self.id

class RemainderHistory (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    sub_total = models.IntegerField(default=0)#av_price*current_remainder
    wholesale_price = models.IntegerField(default=0, null=True)
    av_price = models.IntegerField(default=0, null=True)
    pre_remainder=models.IntegerField(default=0)
    incoming_quantity=models.IntegerField(null=True)
    outgoing_quantity=models.IntegerField(null=True)
    current_remainder = models.IntegerField(default=0)
    retail_price = models.IntegerField(default=0)
    update_check = models.BooleanField(default=False)

    # class Meta:
    #     # ordering = ('created',)  # sorting by date
    #     verbose_name = 'RemainderHistory'
    #     verbose_name_plural = 'remainders'

    def __int__(self):
        return self.id

class RemainderCurrent (models.Model):
    updated = models.DateTimeField(auto_now=True)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    current_remainder = models.IntegerField(default=0)
    av_price = models.IntegerField(null=True)
    total_av_price = models.IntegerField(null=True)
    retail_price = models.IntegerField(default=0, null=True)

    def __int__(self):
        return self.id

class AvPrice (models.Model):
    updated = models.DateTimeField(auto_now=True)
    imei = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    current_remainder = models.IntegerField(default=0)
    av_price = models.IntegerField(null=True)
    sum = models.IntegerField(null=True)

    def __int__(self):
        return self.id


class Register (models.Model):
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)#serves to pass the shop in payment
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(default=1)
    price = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)
   
    def __int__(self):
        return self.id

