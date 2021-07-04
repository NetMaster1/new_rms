from django.contrib import admin
from . models import Document, Delivery, Sale, Transfer, RemainderHistory, RemainderCurrent, Register, Identifier

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category','name', 'imei', 'shop', 'quantity', 'price', 'sub_total')

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name', 'imei', 'shop', 'quantity', 'price', 'sub_total', 'user', 'staff_bonus' )

class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'name', 'imei', 'shop_sender', 'shop_receiver', 'quantity', 'price' )

class RemainderHistoryAdmin(admin.ModelAdmin):
    list_display = ('created', 'category', 'shop', 'name', 'imei', 'pre_remainder', 'incoming_quantity', 'outgoing_quantity', 'current_remainder', 'av_price', 'sub_total', 'retail_price')   

class RemainderCurrentAdmin(admin.ModelAdmin):
    list_display = ('updated', 'shop', 'imei', 'current_remainder')  

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

class RegisterAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'identifier')

class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Transfer, TransferAdmin)
admin.site.register(RemainderHistory, RemainderHistoryAdmin)
admin.site.register(RemainderCurrent, RemainderCurrentAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Register, RegisterAdmin)
admin.site.register(Identifier, IdentifierAdmin)



