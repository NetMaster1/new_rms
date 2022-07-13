from django.contrib import admin
from . models import PayCardReport, ProductHistory, ReportTemp, ReportTempId, DailySaleRep, SaleReport, MonthlyBonus, Sim_report


class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'name', 'imei', 'quantity_in', 'quantity_out')

class ReportTempIdAdmin(admin.ModelAdmin):
    list_display = ('id', 'created')

class ReportTempAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'imei', 'name', 'initial_remainder', 'quantity_in', 'quantity_out', 'end_remainder')

class DailySaleRepAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'created', 'shop', 'cash_move')

class PayCardReportAdmin(admin.ModelAdmin):
    list_display = ('id',)
    
class SaleReportAdmin(admin.ModelAdmin):
    list_display = ('id',)

class MonthlyBonusAdmin(admin.ModelAdmin):
    list_display = ('id',)

class Sim_reportAdmin(admin.ModelAdmin):
    list_display = ('name', 'imei', 'shop', 'date')


admin.site.register(ProductHistory, ProductHistoryAdmin)
admin.site.register(ReportTemp, ReportTempAdmin)
admin.site.register(ReportTempId, ReportTempIdAdmin)
admin.site.register(DailySaleRep, DailySaleRepAdmin)
admin.site.register(PayCardReport, PayCardReportAdmin)
admin.site.register(SaleReport, SaleReportAdmin)
admin.site.register(MonthlyBonus, MonthlyBonusAdmin)
admin.site.register(Sim_report, Sim_reportAdmin)