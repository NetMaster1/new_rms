from django.db import models
from django.contrib.auth.models import User
from app_reference.models import Shop, Expense, Voucher, DocumentType, Contributor
from app_product.models import Document
# import datetime
from datetime import datetime, date
from django.utils import timezone

# Create your models here.

class Cash (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)#creator of the document
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    cho_type = models.ForeignKey(DocumentType, on_delete=models.DO_NOTHING, null=True)
    cash_contributor = models.ForeignKey(Contributor, null=True, on_delete=models.DO_NOTHING, related_name='contributor')
    shop = models.ForeignKey(Shop, on_delete=models.DO_NOTHING)
    pre_remainder= models.IntegerField(default=0)
    cash_in= models.IntegerField(default=0)
    cash_out= models.IntegerField(default=0)
    current_remainder= models.IntegerField(default=0)
    cash_receiver= models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, related_name='cash_receiver')
    cash_off_reason = models.ForeignKey(Expense, on_delete=models.DO_NOTHING, null=True)
    cash_in_reason = models.ForeignKey(Voucher, on_delete=models.DO_NOTHING, null=True)
    sender = models.BooleanField(default=False)#True fo cho from shop_sender

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

#temporary register for storing cash, card, credit when unposting the sale document
class PaymentRegister (models.Model):
    created = models.DateField(auto_now_add=True)
    document = models.ForeignKey(Document, null=True, on_delete=models.DO_NOTHING)
    cash= models.IntegerField(default=0)
    card= models.IntegerField(default=0)
    credit= models.IntegerField(default=0)
 
    def __int__(self):
        return self.id