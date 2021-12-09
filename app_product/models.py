from django.db import models
from django.contrib.auth.models import User
from django.db.models import manager
from app_reference.models import Shop, Supplier, Product, ProductCategory, DocumentType, Contributor, Voucher, Expense

# import datetime
from datetime import datetime, date
from django.utils import timezone


# import pytz


# Create your models here.
class Identifier(models.Model):
    def __int__(self):
        return self.id


class Document(models.Model):
    title = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    sum = models.IntegerField(null=True)
    posted = models.BooleanField(default=False)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)

    def __int__(self):
        return self.id

    # def __str__(self):
    #    return self.title.name

    # class Meta:
    #     ordering = ('created',)  # sorting by date
    #     verbose_name = self.title


class Register(models.Model):
    number = models.IntegerField(null=True)
    created = models.DateTimeField(default=timezone.now, null=True)
    # serves to pass the shop in payment
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop")
    # serves to pass the shop in sales/transfer/sign_off
    shop_sender = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop_sender")
    # serves to pass the shop in delivery/transfer/return
    shop_receiver = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING, related_name="shop_receiver")
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    product = models.ForeignKey(Product, null=True, on_delete=models.DO_NOTHING)
    imei=models.CharField(max_length=250, null=True)
    name=models.CharField(max_length=250, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    quantity = models.IntegerField(default=1)
    current_price = models.IntegerField(null=True)#used for revalutaion document
    price = models.IntegerField(default=0)
    contributor = models.ForeignKey(Contributor, null=True, on_delete=models.DO_NOTHING)
    cash_receiver = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)
    voucher = models.ForeignKey(Voucher, null=True, on_delete=models.DO_NOTHING)
    expense = models.ForeignKey(Expense, null=True, on_delete=models.DO_NOTHING)
    sub_total = models.IntegerField(default=0)
    new = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def __int__(self):
        return self.id


class Delivery(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, related_name="delivery")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING, blank=True)
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING, null=True)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)  # counter
    quantity = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "delivery"
        verbose_name_plural = "deliveries"

    # def sub_total(self):
    #     return self.price * self.quantity

    def __int__(self):
        return self.id


class Returning(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    # supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    # category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)  # retail price
    quantity = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "return"
        verbose_name_plural = "returns"

    # def sub_to):
    #     return self.price * self.quantity

    def __int__(self):
        return self.id


class Recognition(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(
        Document, on_delete=models.DO_NOTHING, related_name="recognition"
    )
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.DO_NOTHING, null=True
    )
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)  #
    quantity = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "recognition"
        verbose_name_plural = "recognitions"

    # def sub_total(self):
    #     return self.price * self.quantity

    def __int__(self):
        return self.id


class SignOff(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    # category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)
    quantity = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "signoff"
        verbose_name_plural = "signoffs"

    # def sub_total(self):
    #     return self.price * self.quantity

    def __int__(self):
        return self.id


class Revaluation(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    # category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price_current = models.IntegerField(default=0)
    price_new = models.IntegerField(default=0)
    # quantity = models.IntegerField(default=0)
    # sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "revaluation"
        verbose_name_plural = "revaluations"

    # def sub_total(self):
    #     return self.price * self.quantity

    def __int__(self):
        return self.id


class Sale(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    category = models.ForeignKey(
        ProductCategory, null=True, on_delete=models.DO_NOTHING
    )
    date = models.DateTimeField(default=timezone.now, blank=True)
    identifier = models.ForeignKey(
        Identifier, null=True, blank=True, on_delete=models.DO_NOTHING
    )
    supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.DO_NOTHING
    )
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    price = models.DecimalField(default=0, max_digits=8, decimal_places=2)
    quantity = models.IntegerField(default=0)
    sub_total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    staff_bonus = models.IntegerField(default=0)
    user = models.ForeignKey(User, null=True, on_delete=models.DO_NOTHING)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "sale"
        verbose_name_plural = "sales"

    # def sub_total(self):
    #     return int(self.price) * int(self.quantity)

    def __int__(self):
        return self.id


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


class Transfer(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=250)
    shop_sender = models.ForeignKey(
        Shop, related_name="sender_shop", on_delete=models.DO_NOTHING
    )
    shop_receiver = models.ForeignKey(
        Shop, related_name="receiver_shop", on_delete=models.DO_NOTHING
    )
    imei = models.CharField(max_length=250)
    price = models.IntegerField(default=0)  # counter
    quantity = models.IntegerField(default=0)
    sub_total = models.IntegerField(default=0)

    class Meta:
        # ordering = ('created',)  # sorting by date
        verbose_name = "transfer"
        verbose_name_plural = "transfers"

    def __int__(self):
        return self.id


class RemainderHistory(models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    document = models.ForeignKey(Document, on_delete=models.DO_NOTHING, null=True)
    rho_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.DO_NOTHING)
    product_id = models.ForeignKey(Product, on_delete=models.DO_NOTHING, null=True)
    name = models.CharField(max_length=250)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    imei = models.CharField(max_length=250)
    sub_total = models.IntegerField(default=0)  # av_price*current_remainder
    wholesale_price = models.IntegerField(default=0, null=True)
    av_price = models.IntegerField(default=0, null=True)
    pre_remainder = models.IntegerField(default=0)
    incoming_quantity = models.IntegerField(null=True)
    outgoing_quantity = models.IntegerField(null=True)
    current_remainder = models.IntegerField(default=0)
    retail_price = models.IntegerField(default=0)
    update_check = models.BooleanField(default=False)
    status = models.BooleanField(default=False)  # "False" for Transfer(send) "True" for Transfer(receive)

    # class Meta:
    #     # ordering = ('created',)  # sorting by date
    #     verbose_name = 'RemainderHistory'
    #     verbose_name_plural = 'remainders'

    def __int__(self):
        return self.id


class RemainderCurrent(models.Model):
    updated = models.DateTimeField(auto_now=True)
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    category = models.ForeignKey(ProductCategory, on_delete=models.DO_NOTHING, null=True)
    imei = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    current_remainder = models.IntegerField(default=0)
    av_price = models.IntegerField(null=True)
    total_av_price = models.IntegerField(null=True)
    retail_price = models.IntegerField(default=0, null=True)

    def __int__(self):
        return self.id


class AvPrice(models.Model):
    updated = models.DateTimeField(auto_now=True)
    imei = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    current_remainder = models.IntegerField(default=0)
    av_price = models.IntegerField(null=True)
    sum = models.IntegerField(null=True)

    def __int__(self):
        return self.id
