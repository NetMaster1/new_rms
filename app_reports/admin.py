from django.contrib import admin
from . models import ProductHistory, ReportTemp, ReportTempId


class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'name', 'imei', 'quantity_in', 'quantity_out')

class ReportTempIdAdmin(admin.ModelAdmin):
    list_display = ('id', 'created')

class ReportTempAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'imei', 'name', 'initial_remainder', 'quantity_in', 'quantity_out', 'end_remainder')


admin.site.register(ProductHistory, ProductHistoryAdmin)
admin.site.register(ReportTemp, ReportTempAdmin)
admin.site.register(ReportTempId, ReportTempIdAdmin)