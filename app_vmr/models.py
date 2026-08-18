from django.db import models
from django.contrib.auth.models import User
from app_reference.models import ProductCategory, Supplier, Product, Shop, DocumentType

# import datetime
from datetime import datetime, date
from django.utils import timezone

# Create your models here.
# class VMR_criteria (models.Model):
#     client_problem_resolution = models.BooleanField(default=False)
#     MNP_offer = models.BooleanField(default=False)
#     sim_offer = models.BooleanField(default=False)
#     mix_offer = models.BooleanField(default=False)
#     phone_offer = models.BooleanField(default=False)

#     def __int__(self):
#         return self.id

class VMR_check (models.Model):
    created = models.DateTimeField(default=timezone.now, null=True)
    shop = models.CharField(max_length=50, null=True)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)
    client_problem_res = models.BooleanField(default=False)
    mnp_offer = models.BooleanField(default=False)
    rtc_offer = models.BooleanField(default=False)
    sim_offer = models.BooleanField(default=False)
    mixx_offer = models.BooleanField(default=False)
    phone_offer = models.BooleanField(default=False)

   
    # class Meta:
    #     ordering = ('created',)  # sorting by date
    def __int__(self):
        return self.id
   
