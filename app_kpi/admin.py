from django.contrib import admin
from . models import KPIMonthlyPlan, KPI_performance

# Register your models here.
class KPIMonthlyPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'month_reported', 'year_reported')

class KPI_PerformanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'month_reported', 'year_reported')


admin.site.register(KPIMonthlyPlan, KPIMonthlyPlanAdmin)
admin.site.register(KPI_performance, KPI_PerformanceAdmin)