from django.contrib import admin
from . models import ProductHistory


class ProductHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'name', 'imei', 'quantity_in', 'quantity_out')


admin.site.register(ProductHistory, ProductHistoryAdmin)