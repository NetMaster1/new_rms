from django.db import models
# import datetime
from datetime import datetime, date
from django.utils import timezone

# Create your models here.


class Contributor (models.Model):
    name = models.CharField(max_length=250)

    def __int__(self):
        return self.id

class Supplier (models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Shop (models.Model):
    name = models.CharField(max_length=50)
    TID = models.CharField(max_length=50, null=True)#acquiring terminal number (TID)
    commission=models.DecimalField(max_digits=3, decimal_places=2, default=2.1)#acquiring terminal commission rate
    sale_k=models.DecimalField(max_digits=3, decimal_places=2, default=1)
    retail = models.BooleanField(default=True)#mark for retail shops
    active = models.BooleanField(default=True)#mark for active shops
    offline = models.BooleanField(default=True)#mark for offline shops to cut off ozon
    subdealer = models.BooleanField(default=False)#mark for subdealer shops. False for our shops. True for subdealer shops
    MB = models.BooleanField(default=True)#mark for monobrand shops
    cash_register = models.BooleanField(default=True)#mark for monobrand without cash register. False means the shop is equipped with e-rms cash register
    shift_status = models.BooleanField(default=False)# shows shift status. False means shift is open.
    shift_status_updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ('name',)  # sorting by name

    def __str__(self):
        return self.name
    

# class Subdealer (models.Model):
#     name = models.CharField(max_length=50)

#     class Meta:
#         ordering = ('name',)  # sorting by name

#     def __str__(self):
#         return self.name

class ProductCategory (models.Model):
    name = models.CharField(max_length=250)
    bonus_percent=models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return self.name

class Services (models.Model):
    name = models.CharField(max_length=250)
    retail_price = models.IntegerField(default=0, null=True)
    bonus_percent=models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return self.name

class DocumentType (models.Model):
    name = models.CharField(max_length=250)

    class Meta:
        verbose_name='documentType'
    def __str__(self):
        return self.name

class Product (models.Model):
    created = models.DateTimeField(auto_now=True)
    emumerator = models.IntegerField(null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=80)
    imei = models.CharField(max_length=50, unique=True)
    #status = models.BooleanField(default=False)  # "True" for sent to T2 (for sim_cards)
    

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def __str__(self):
        return self.name

class Expense (models.Model):
    name = models.CharField(max_length=50, null=True)
    
    def __str__(self):
        return self.name

class Voucher (models.Model):
    name = models.CharField(max_length=50, null=True)

    def __str__(self):
        return self.name
    
class Teko_pay (models.Model):
    name = models.CharField(max_length=50, null=True)
    
    def __str__(self):
        return self.name
    
class Month (models.Model):
    #key = models.CharField(max_length=10)
    number_of_days = models.IntegerField(null=True)
    name = models.CharField(max_length=20)
    def __str__(self):
        return self.name
    
class Year (models.Model):
    #key = models.CharField(max_length=10)
    name = models.CharField(max_length=10)
    def __str__(self):
        return self.name