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
    #identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    month_reported = models.ForeignKey(Month, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    year_reported = models.ForeignKey(Year, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    GI = models.IntegerField(default=0, null=True)
    MNP = models.IntegerField(default=0, null=True)
    HighBundle = models.IntegerField(default=0, null=True)#фокусные тарифы
    HomeInternet_T2 = models.IntegerField(default=0, null=True)
    HomeInternet_RT = models.IntegerField(default=0, null=True)
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
    
class GI_report(models.Model):
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    month_reported = models.ForeignKey(Month, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    year_reported = models.ForeignKey(Year, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    GI_plan = models.IntegerField(default=0, null=True)
    GI = models.IntegerField(default=0, null=True)
    date_before_current = models.IntegerField(default=0, null=True)
    days_of_the_month = models.IntegerField(default=0, null=True)
    def __int__(self):
        return self.id
    def forecast_percent(self):
        if self.GI_plan==0:
            return 0
        else:
            return int((self.GI/self.date_before_current*self.days_of_the_month)/self.GI_plan*100)
    def forecast_items(self):
        return int(self.GI/self.date_before_current*self.days_of_the_month)
    def average_per_day(self):
        if (self.days_of_the_month-self.date_before_current)==0:
            return int(0)
        else:
            return int((self.GI_plan - self.GI)/(self.days_of_the_month-self.date_before_current))


class Focus_report(models.Model):
    identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
    month_reported = models.ForeignKey(Month, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    year_reported = models.ForeignKey(Year, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
    shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
    focus_plan = models.IntegerField(default=0, null=True)
    focus = models.IntegerField(default=0, null=True)
    date_before_current = models.IntegerField(default=0, null=True)
    days_of_the_month = models.IntegerField(default=0, null=True)
    def __int__(self):
        return self.id
    def forecast_percent(self):
        if self.focus_plan==0:
            return 0
        else:
            return int((self.focus/self.date_before_current*self.days_of_the_month)/self.focus_plan*100)
    def forecast_items(self):
        return int(self.focus/self.date_before_current*self.days_of_the_month)
    def average_per_day(self):
        if (self.days_of_the_month-self.date_before_current)==0:
            return int(0)
        else:
            return int((self.focus_plan - self.focus)/(self.days_of_the_month-self.date_before_current))


    class KPI_Forecast(models.Model):
        #identifier = models.ForeignKey(Identifier, null=True, on_delete=models.DO_NOTHING)
        month_reported = models.ForeignKey(Month, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
        year_reported = models.ForeignKey(Year, null=True, on_delete=models.DO_NOTHING)#Отчетный месяц
        shop = models.ForeignKey(Shop, null=True, on_delete=models.DO_NOTHING)
        GI = models.IntegerField(default=0, null=True)
        MNP = models.IntegerField(default=0, null=True)
        HighBundle = models.IntegerField(default=0, null=True)#фокусные тарифы
        HomeInternet_T2 = models.IntegerField(default=0, null=True)
        HomeInternet_RT = models.IntegerField(default=0, null=True)
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
