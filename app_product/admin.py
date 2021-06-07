from django.contrib import admin
from . models import Document, Delivery, Sale, Remainder

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category','name', 'imei', 'shop', 'quantity_plus')

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'imei', 'shop', 'quantity_minus')

class RemainderAdmin(admin.ModelAdmin):
    list_display = ('category', 'shop', 'name', 'imei', 'quantity_remainder')    

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Remainder, RemainderAdmin)
admin.site.register(Document, DocumentAdmin)


