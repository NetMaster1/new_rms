from django.contrib import admin
from . models import Document, Delivery, Sale, Transfer, Remainder, Register, Identifier

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category','name', 'imei', 'shop', 'quantity', 'price', 'sub_total')

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name', 'imei', 'shop', 'quantity', 'price', 'sub_total', 'user' )

class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'name', 'imei', 'shop_sender', 'shop_receiver', 'quantity', 'price' )

class RemainderAdmin(admin.ModelAdmin):
    list_display = ('category', 'shop', 'name', 'imei', 'quantity_remainder', 'av_price', 'sub_total', 'retail_price')    

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

class RegisterAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'identifier')

class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Transfer, TransferAdmin)
admin.site.register(Remainder, RemainderAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Register, RegisterAdmin)
admin.site.register(Identifier, IdentifierAdmin)



