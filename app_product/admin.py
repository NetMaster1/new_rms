from django.contrib import admin
from . models import Document, Delivery, Sale, Transfer, RemainderHistory, RemainderCurrent, Register, Identifier

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category','name', 'imei', 'shop', 'quantity', 'price', 'sub_total')
    ordering = ('-created',)

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category', 'name', 'imei', 'shop', 'quantity', 'price', 'sub_total', 'user', 'staff_bonus' )

class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop_sender', 'shop_receiver', 'quantity', 'price' )

class RemainderHistoryAdmin(admin.ModelAdmin):
    list_display = ('created', 'category', 'document', 'shop', 'name', 'imei', 'pre_remainder', 'incoming_quantity', 'outgoing_quantity', 'current_remainder', 'av_price', 'sub_total', 'retail_price', 'update_check') 
    list_filter = ('imei',)
    ordering = ('-created',)

    # def get_ordering(self, request):
    #     if request.user.is_superuser:
    #         return ('imei', '-created')
    #     else:
    #         return ('imei',)

class RemainderCurrentAdmin(admin.ModelAdmin):
    list_display = ('updated', 'shop', 'name', 'imei', 'current_remainder', 'retail_price')  

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



