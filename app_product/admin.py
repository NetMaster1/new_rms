from django.contrib import admin
from . models import Document, Delivery, Sale, Transfer, RemainderHistory, RemainderCurrent, Register, Identifier, AvPrice

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'supplier' ,'name', 'imei', 'shop', 'quantity', 'price', 'sub_total')
    ordering = ('-created',)
    list_filter = ('imei',)

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category', 'name', 'imei', 'shop', 'quantity', 'price', 'sub_total', 'user', 'staff_bonus' )

class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop_sender', 'shop_receiver', 'quantity', 'price' )

class RemainderHistoryAdmin(admin.ModelAdmin):
    list_display = ('created', 'document', 'shop', 'name', 'imei', 'pre_remainder', 'incoming_quantity', 'outgoing_quantity', 'wholesale_price', 'current_remainder') 
    list_filter = ('imei', 'document', 'shop')
    ordering = ('-created',)

    # def get_ordering(self, request):
    #     if request.user.is_superuser:
    #         return ('imei', '-created')
    #     else:
    #         return ('imei',)

class RemainderCurrentAdmin(admin.ModelAdmin):
    list_display = ('updated', 'shop', 'name', 'imei', 'current_remainder', 'av_price', 'total_av_price', 'retail_price')  
    list_filter = ('imei',)

class AvPriceAdmin(admin.ModelAdmin):
    list_display = ('updated', 'name', 'imei', 'current_remainder', 'av_price', 'sum')  
    list_filter = ('imei',)

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created' , 'user', 'sum')
    ordering = ('-created',)

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
admin.site.register(AvPrice, AvPriceAdmin)




