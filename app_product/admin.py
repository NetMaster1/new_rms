from django.contrib import admin
from . models import Document, Delivery, Recognition, Sale, Transfer, SignOff, Returning, Revaluation, RemainderHistory, RemainderCurrent, Register, Identifier, AvPrice

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'supplier' ,'name', 'imei', 'shop', 'quantity', 'price', 'sub_total')
    ordering = ('-created',)
    list_filter = ('imei',)

class RecognitionAdmin(admin.ModelAdmin):
    list_display = ('id', 'created','name', 'imei', 'shop', 'quantity', 'price', 'sub_total')
    ordering = ('-created',)
    list_filter = ('imei',)

class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'category', 'name', 'imei', 'shop', 'quantity', 'price', 'sub_total', 'user', 'staff_bonus' )

class TransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop_sender', 'shop_receiver', 'quantity', 'price' )

class SignOffAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop', 'quantity' )

class ReturningAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop', 'quantity' )

class RevaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop')

class RemainderHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document','supplier', 'rho_type', 'status', 'shop', 'category', 'name', 'imei', 'pre_remainder', 'incoming_quantity', 'outgoing_quantity', 'current_remainder', 'wholesale_price', 'retail_price', 'user', 'inventory_doc') 
    list_filter = ('imei', 'document', 'shop')
    ordering = ('-created',)
    list_per_page=25
    list_select_related = True
    # def get_ordering(self, request):
    #     if request.user.is_superuser:
    #         return ('imei', '-created')
    #     else:
    #         return ('imei',)

class RemainderCurrentAdmin(admin.ModelAdmin):
    list_display = ('updated','shop', 'category', 'name', 'imei', 'current_remainder', 'retail_price')  
    list_filter = ('imei',)

class AvPriceAdmin(admin.ModelAdmin):
    list_display = ('updated', 'name', 'imei', 'current_remainder', 'av_price', 'sum')  
    list_filter = ('imei',)

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created' , 'user', 'sum', 'base_doc')
    ordering = ('-created',)

class RegisterAdmin(admin.ModelAdmin):
    list_display = ('created', 'document', 'doc_type', 'shop_sender', 'shop_receiver', 'product', 'sub_total', 'identifier', 'new', 'deleted')

class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'created')

admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(Recognition, RecognitionAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Transfer, TransferAdmin)
admin.site.register(SignOff, SignOffAdmin)
admin.site.register(Returning, ReturningAdmin)
admin.site.register(Revaluation, RevaluationAdmin)
admin.site.register(RemainderHistory, RemainderHistoryAdmin)
admin.site.register(RemainderCurrent, RemainderCurrentAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Register, RegisterAdmin)
admin.site.register(Identifier, IdentifierAdmin)
admin.site.register(AvPrice, AvPriceAdmin)




