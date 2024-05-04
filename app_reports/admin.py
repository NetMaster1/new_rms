from django.contrib import admin
from . models import AcquiringReport, PayCardReport, ProductHistory, ReportTemp, ReportTempId, DailySaleRep, SaleReport, MonthlyBonus, Sim_report, ClientReport, SalaryReport, ClientHistoryReport


class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'name', 'imei', 'quantity_in', 'quantity_out')

class AcquiringReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'TID', 'sum_bank', 'sum_retail',)

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
    list_per_page=500

class ClientReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'phone', 'user', 'cashback_awarded', 'cashback_off', 'cashback_remaining' ) 
    list_per_page=50

class ClientHistoryReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'user', 'number_of_docs', 'sum', ) 
    list_per_page=500

class SalaryReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'user', 'sum') 
   


admin.site.register(ProductHistory, ProductHistoryAdmin)
admin.site.register(AcquiringReport, AcquiringReportAdmin)
admin.site.register(ReportTemp, ReportTempAdmin)
admin.site.register(ReportTempId, ReportTempIdAdmin)
admin.site.register(DailySaleRep, DailySaleRepAdmin)
admin.site.register(PayCardReport, PayCardReportAdmin)
admin.site.register(SaleReport, SaleReportAdmin)
admin.site.register(MonthlyBonus, MonthlyBonusAdmin)
admin.site.register(Sim_report, Sim_reportAdmin)
admin.site.register(ClientReport, ClientReportAdmin)
admin.site.register(ClientHistoryReport, ClientHistoryReportAdmin)
admin.site.register(SalaryReport, SalaryReportAdmin)