from django.db import models
from app_reference.models import ProductCategory, Supplier

# import datetime
from datetime import datetime, date
from django.utils import timezone


# Create your models here.

class ProductHistory (models.Model):
    document = models.CharField(max_length=50, default=0)
    document_id = models.CharField(max_length=50, default=0)
    shop = models.CharField(max_length=50, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=50)
    imei = models.CharField(max_length=50)
    quantity_in = models.IntegerField(null=True)
    quantity_out = models.IntegerField(null=True)

    # class Meta:
    #     ordering = ('created',)  # sorting by date
    def __str__(self):
        return self.name


    
class ReportTempId (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    existance_check = models.BooleanField(default=True)#service mark
    def __int__(self):
        return self.id

class ReportTemp (models.Model):
    report_id = models.ForeignKey(ReportTempId, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=50, null=True)
    imei = models.CharField(max_length=50, null=True)
    quantity_in = models.IntegerField(null=True)
    quantity_out = models.IntegerField(null=True)
    initial_remainder = models.IntegerField(null=True)
    end_remainder = models.IntegerField(null=True)
    existance_check = models.BooleanField(default=True)#service mark

    def __int__(self):
        #return "{} - {} - {}".format(self.name, self.end_remainder)
        return self.id

class DailySaleRep (models.Model):
    shop = models.CharField(max_length=50, null=True)
    smarphones = models.IntegerField(null=True)
    accessories = models.IntegerField(null=True)
    sim_cards = models.IntegerField(null=True)
    phones = models.IntegerField(null=True)
    iphone = models.IntegerField(null=True)
    insuranсе = models.IntegerField(null=True)
    wink = models.IntegerField(null=True)
    services = models.IntegerField(null=True)
    sub_total = models.IntegerField(null=True)

    def __int__(self):
        #return "{} - {} - {}".format(self.name, self.end_remainder)
        return self.id

    # def sub_total(self):
    #     return self.price * self.quantity