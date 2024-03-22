from pyexpat import model
from django.db import models
from django.contrib.auth.models import User
from django.db.models import manager
from app_reference.models import Shop, Supplier, Product, ProductCategory, DocumentType, Contributor, Voucher, Expense
from app_clients.models import Customer

# import datetime
from datetime import datetime, date
from django.utils import timezone

# import pytz

# Create your models here.
class Identifier(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    def __int__(self):
        return self.id

class Document(models.Model):
    title = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    shop_sender = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name='shop_sender')
    shop_receiver = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop_receiver")#also used for inventory doc
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    base_doc = models.IntegerField(null=True)#link between inventory doc & sign_off & recognition docs
    posted = models.BooleanField(default=False)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    client = models.ForeignKey(Customer, null=True, on_delete=models.DO_NOTHING)
    sum = models.IntegerField(null=True)
    cashback_off=models.IntegerField(default=0)
    sum_minus_cashback=models.IntegerField(null=True, blank=True)

    def __int__(self):
        return self.id

    # def __str__(self):
    #    return self.title.name

    # class Meta:
    #     ordering = ('created',)  # sorting by date
    #     verbose_name = self.title

# class IntegratedDailySaleDoc(models.Model):
#     created = models.DateField(auto_now_add=True, null=True)
#     user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
#     shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)

#     def __int__(self):
#         return self.id


class AvPrice(models.Model):
    updated = models.DateTimeField(auto_now=True)
    imei = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    current_remainder = models.IntegerField(default=0)
    av_price = models.IntegerField(null=True)
    sum = models.IntegerField(null=True)

    def __int__(self):
        return self.id

class Register(models.Model):
    number = models.IntegerField(null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    # serves to pass the shop in sales/payment
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop")
    # serves to pass the shop in transfer/sign_off
    #shop_sender = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop_sender")
    # serves to pass the shop in delivery/transfer/return
    #shop_receiver = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop_receiver")
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, on_delete=models.DO_NOTHING)
    imei=models.CharField(max_length=250, null=True)
    name=models.CharField(max_length=250, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    doc_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    quantity = models.IntegerField(default=1)
    real_quantity = models.IntegerField(null=True)#used for inventory
    price = models.IntegerField(default=0)
    reevaluation_price = models.IntegerField(default=0)#used to reevaluate an item in the process of inventory
    current_price = models.IntegerField(null=True)#used for showing avprice in transfer document
    av_price=models.ForeignKey(AvPrice, null=True, on_delete=models.DO_NOTHING)
    contributor = models.ForeignKey(Contributor, null=True, on_delete=models.DO_NOTHING)
    cash_receiver = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    voucher = models.ForeignKey(Voucher, null=True, on_delete=models.DO_NOTHING)
    expense = models.ForeignKey(Expense, null=True, on_delete=models.DO_NOTHING)
    sub_total = models.BigIntegerField(default=0)
    #cash_back_awarded = models.IntegerField(null=True, blank=True)
    # cash_back_paid = models.IntegerField(null=True, blank=True)
    # client_phone = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, null=True)
    new = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __int__(self):
        return self.id

class InventoryList(models.Model):
    number = models.IntegerField(null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    # serves to pass the shop in sales/payment
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, on_delete=models.DO_NOTHING)
    imei=models.CharField(max_length=250, null=True)
    name=models.CharField(max_length=250, null=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    doc_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    quantity = models.IntegerField(default=1)
    real_quantity = models.IntegerField(null=True)#used for inventory
    price = models.IntegerField(default=0)
    reevaluation_price = models.IntegerField(default=0)#used to reevaluate an item in the process of inventory
    sub_total = models.BigIntegerField(default=0)

    def __int__(self):
        return self.id


# class Revaluation(models.Model):
#     created = models.DateTimeField(default=timezone.now, null=True)
#     document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
#     user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
#     identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
#     # category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
#     name = models.CharField(max_length=250)
#     shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
#     imei = models.CharField(max_length=250)
#     price_current = models.IntegerField(default=0)
#     price_new = models.IntegerField(default=0)
#     # quantity = models.IntegerField(default=0)
#     # sub_total = models.IntegerField(default=0)

#     class Meta:
#         # ordering = ('created',)  # sorting by date
#         verbose_name = "revaluation"
#         verbose_name_plural = "revaluations"

#     # def sub_total(self):
#     #     return self.price * self.quantity

#     def __int__(self):
#         return self.id

class CashOff(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now, null=True)
    date = models.DateTimeField(default=timezone.now, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    sub_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # def sub_total(self):
    #     return int(self.price) * int(self.quantity)

    def __int__(self):
        return self.id

class RemainderHistory(models.Model):
    #temporary utility field for numbering rhos while displaying them at change_sale_posted html page
    number = models.IntegerField(default=0, null=True)#service field for enumerating selected rhos in arrays
    #number = models.IntegerField(default=0, required=False, read_only=True)#just an example
    created = models.DateTimeField(default=timezone.now, null=True)
    #created = models.DateTimeField(format='%Y-%m-%dT%H:%M:%S', default=timezone.now, null=True)
    #created = serializers.DateTimeField(format='iso-8601', required=False, read_only=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    #editor = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='editor', null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, null=True)
    #dsd = models.ForeignKey(IntegratedDailySaleDoc, null=True, on_delete=models.DO_NOTHING) #for compiling a list of sales per day
    inventory_doc = models.ForeignKey(Document, on_delete=models.DO_NOTHING, related_name="inventory" ,null=True, blank=True)
    rho_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.DO_NOTHING)
    product_id = models.ForeignKey(Product, blank=True, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    sub_total = models.IntegerField(default=0)  # av_price/reatail_price/?????*current_remainder
    wholesale_price = models.IntegerField(default=0, null=True)
    av_price = models.IntegerField(default=0, null=True)
    retail_price = models.IntegerField(default=0)
    pre_remainder = models.IntegerField(default=0)
    incoming_quantity = models.IntegerField(null=True)
    outgoing_quantity = models.IntegerField(null=True)
    current_remainder = models.BigIntegerField(default=0)
    update_check = models.BooleanField(default=False)
    status = models.BooleanField(default=False)  # "False" for Transfer(send) "True" for Transfer(receive)
    cash_back_awarded = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ('-created',)  # sorting by date
    #     verbose_name = 'RemainderHistory'
    #     verbose_name_plural = 'remainders'

    def retail_sum_outgoing(self):
        return self.retail_price * self.outgoing_quantity

    def retail_sum_incoming(self):
        return self.retail_price * self.incoming_quantity

    def __int__(self):
        return self.id




class RemainderCurrent(models.Model):
    updated = models.DateTimeField(auto_now=True)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    imei = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    current_remainder = models.IntegerField(default=0)
    retail_price = models.IntegerField(default=0, null=True)

    class Meta:
        ordering = ('category', 'name',)  # sorting by date

    def __int__(self):
        return self.id

class TradeIn(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, null=True)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING, null=True)
    imei = models.CharField(max_length=250)
    model = models.CharField(max_length=250, null=True)
    cost = models.IntegerField(null=True)

    def __int__(self):
        return self.id