from django.contrib import admin
from . models import Document,  Revaluation, RemainderHistory, Register, Identifier, AvPrice 

class RevaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'name', 'imei', 'shop')

class RemainderHistoryAdmin(admin.ModelAdmin):
    list_display = ('id','document', 'created', 'updated', 'rho_type', 'status', 'shop', 'category', 'name', 'imei', 'pre_remainder', 'incoming_quantity', 'outgoing_quantity', 'current_remainder', 'wholesale_price', 'retail_price', 'user', 'inventory_doc') 
    list_filter = ('imei', 'document', 'shop', 'rho_type')
    ordering = ('-created',)
    list_per_page=25
    list_select_related = True
    # def get_ordering(self, request):
    #     if request.user.is_superuser:
    #         return ('imei', '-created')
    #     else:
    #         return ('imei',)

class AvPriceAdmin(admin.ModelAdmin):
    list_display = ('updated', 'name', 'imei', 'current_remainder', 'av_price', 'sum')  
    list_filter = ('imei',)

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created' , 'user', 'sum', 'base_doc')
    ordering = ('-created',)

class RegisterAdmin(admin.ModelAdmin):
    list_display = ('created', 'document', 'doc_type', 'product', 'sub_total', 'identifier', 'new', 'deleted')

class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'created')

#admin.site.register(Delivery, DeliveryAdmin)
#admin.site.register(Recognition, RecognitionAdmin)
#admin.site.register(Sale, SaleAdmin)
#admin.site.register(Transfer, TransferAdmin)
#admin.site.register(SignOff, SignOffAdmin)
#admin.site.register(Returning, ReturningAdmin)
admin.site.register(Revaluation, RevaluationAdmin)
admin.site.register(RemainderHistory, RemainderHistoryAdmin)
#admin.site.register(RemainderCurrent, RemainderCurrentAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Register, RegisterAdmin)
admin.site.register(Identifier, IdentifierAdmin)
admin.site.register(AvPrice, AvPriceAdmin)




