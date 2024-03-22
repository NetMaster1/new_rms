from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from app_product.models import Document
from app_reference.models import DocumentType, Shop
# Create your models here.

class MonthlyPlanKPI(models.Model):
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    GI = models.IntegerField(default=0, null=True)
    MNP = models.IntegerField(default=0, null=True)
    HI = models.IntegerField(default=0, null=True)
    RT_equip_item = models.IntegerField(default=0, null=True)#number of pieces
    RT_equip_roubles = models.IntegerField(default=0, null=True)#sum of money
    wink_item = models.IntegerField(default=0, null=True)#number of pieces
    wink_roubles = models.IntegerField(default=0, null=True)#sum of money
    upsale= models.IntegerField(default=0, null=True)
    mixx= models.IntegerField(default=0, null=True)
    gold_sim= models.IntegerField(default=0, null=True)

    def __int__(self):
        return self.id
