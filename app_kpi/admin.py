from django.contrib import admin
from . models import KPIMonthlyPlan, KPI_performance, GI_report

# Register your models here.
class KPIMonthlyPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'month_reported', 'year_reported', 'shop')

class KPI_PerformanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'month_reported', 'year_reported', 'shop')

class GI_reportAdmin(admin.ModelAdmin):
    list_display = ('id', 'month_reported', 'year_reported', 'shop', 'GI')


admin.site.register(KPIMonthlyPlan, KPIMonthlyPlanAdmin)
admin.site.register(KPI_performance, KPI_PerformanceAdmin)
admin.site.register(GI_report, GI_reportAdmin)