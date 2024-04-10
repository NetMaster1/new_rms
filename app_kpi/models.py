from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from app_product.models import Identifier, Document
from app_reference.models import DocumentType, Shop, Month, Year
# Create your models here.

class KPIMonthlyPlan(models.Model):
    shop = models.CharField(max_length=25, null=True)
    month_reported = models.CharField(max_length=25, null=True)
    year_reported = models.CharField(max_length=10, null=True)
    #shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    # month_reported = models.ForeignKey(Month, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    # year_reported = models.ForeignKey(Year, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    GI = models.IntegerField(default=0, null=True)
    MNP = models.IntegerField(default=0, null=True)
    HighBundle = models.IntegerField(default=0, null=True)#фокусные тарифы
    HomeInternet = models.IntegerField(default=0, null=True)
    smartphones_sum = models.IntegerField(default=0, null=True)
    RT_active_cam = models.IntegerField(default=0, null=True)#number of pieces
    RT_equip_roubles = models.IntegerField(default=0, null=True)#sum of money
    wink_item = models.IntegerField(default=0, null=True)#number of pieces
    wink_roubles = models.IntegerField(default=0, null=True)#sum of money
    upsale= models.IntegerField(default=0, null=True)
    mixx= models.IntegerField(default=0, null=True)
    golden_sim= models.IntegerField(default=0, null=True)
    insurance_charge= models.IntegerField(default=0, null=True)#оплата страховки

    def __int__(self):
        return self.id
    
class KPI_performance(models.Model):
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    month_reported = models.ForeignKey(Month, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    year_reported = models.ForeignKey(Year, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    GI = models.IntegerField(default=0, null=True)
    MNP = models.IntegerField(default=0, null=True)
    HighBundle = models.IntegerField(default=0, null=True)#фокусные тарифы
    HomeInternet = models.IntegerField(default=0, null=True)
    smartphones_sum = models.IntegerField(default=0, null=True)
    RT_active_cam = models.IntegerField(default=0, null=True)#number of pieces
    RT_equip_roubles = models.IntegerField(default=0, null=True)#sum of money
    wink_item = models.IntegerField(default=0, null=True)#number of pieces
    wink_roubles = models.IntegerField(default=0, null=True)#sum of money
    upsale= models.IntegerField(default=0, null=True)
    mixx= models.IntegerField(default=0, null=True)
    golden_sim= models.IntegerField(default=0, null=True)
    insurance_charge= models.IntegerField(default=0, null=True)#оплата страховки

    def __int__(self):
        return self.id
