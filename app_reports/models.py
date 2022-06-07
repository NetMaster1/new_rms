from django.db import models
from django.contrib.auth.models import User
from app_reference.models import ProductCategory, Supplier, Product, Shop

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
    price = models.IntegerField(null=True)
    initial_remainder = models.IntegerField(null=True)
    end_remainder = models.IntegerField(null=True)
    existance_check = models.BooleanField(default=True)#service mark

    def __int__(self):
        #return "{} - {} - {}".format(self.name, self.end_remainder)
        return self.id

class DailySaleRep (models.Model):
    report_id = models.ForeignKey(ReportTempId, on_delete=models.DO_NOTHING, null=True)
    shop = models.CharField(max_length=50, null=True)
    created = models.CharField(max_length=50, null=True)
    #shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    #category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    #sum = models.IntegerField(default=0)
    opening_balance = models.IntegerField(null=True)
    smartphones = models.IntegerField(null=True)
    accessories = models.IntegerField(null=True)
    sim_cards = models.IntegerField(null=True)
    pay_cards = models.IntegerField(null=True)
    phones = models.IntegerField(null=True)
    iphone = models.IntegerField(null=True)
    insuranсе = models.IntegerField(null=True)
    wink = models.IntegerField(null=True)
    services = models.IntegerField(null=True)
    gadgets = models.IntegerField(null=True)
    modems = models.IntegerField(null=True)
    net_sales = models.IntegerField(null=True)
    #sub_total = models.IntegerField(null=True)
    credit = models.IntegerField(null=True)
    card = models.IntegerField(null=True)
    salary = models.IntegerField(null=True)
    expenses = models.IntegerField(null=True)
    cash_move = models.IntegerField(null=True)
    return_sum = models.IntegerField(null=True)
    final_balance = models.IntegerField(null=True)

    def __int__(self):
        #return "{} - {} - {}".format(self.name, self.end_remainder)
        return self.id

    #def sub_total(self):
    #     return self.price * self.quantity

class MonthlyBonus (models.Model):
    #user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    user_name = models.CharField(max_length=50, null=True)
    smarphones = models.IntegerField(null=True)
    accessories = models.IntegerField(null=True)
    sim_cards = models.IntegerField(null=True)
    phones = models.IntegerField(null=True)
    iphone = models.IntegerField(null=True)
    insuranсе = models.IntegerField(null=True)
    wink = models.IntegerField(null=True)
    services = models.IntegerField(null=True)
    credit = models.IntegerField(null=True)
    sub_total = models.IntegerField(null=True)
    
    def __int__(self):
        #return "{} - {} - {}".format(self.name, self.end_remainder)
        return self.id

    # def sub_total(self):
    #     return self.price * self.quantity

class SaleReport (models.Model):
    report_id = models.ForeignKey(ReportTempId, on_delete=models.DO_NOTHING, null=True)
    #category = models.CharField(max_length=50, null=True)#this field is needed to place SaleReports ordered by Category
    product = models.CharField(max_length=50, null=True)
    av_sum = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    retail_sum = models.IntegerField(default=0)
    margin = models.IntegerField(default=0)

    def __int__(self):
        return self.id

class PayCardReport (models.Model):
    report_id = models.ForeignKey(ReportTempId, on_delete=models.DO_NOTHING, null=True)
    shop = models.CharField(max_length=50, null=True)
    created = models.DateTimeField(auto_now_add=True)
    product = models.CharField(max_length=50, null=True)
    pre_remainder = models.IntegerField(default=0)
    incoming_quantity = models.IntegerField(default=0)
    outgoing_quantity = models.IntegerField(default=0)
    current_remainder = models.IntegerField(default=0)

    def __int__(self):
        return self.id