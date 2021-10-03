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

    def __int__(self):
        return self.id