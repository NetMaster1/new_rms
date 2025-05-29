from django.contrib import admin
from . models import Document, RemainderHistory, RemainderCurrent, Register, Identifier, AvPrice, InventoryList

# class RevaluationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'created', 'document', 'name', 'imei', 'shop')

class RemainderHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'time_seconds', 'document', 'rho_type', 'status', 'shop', 'category', 'name', 'imei', 'ean', 'pre_remainder', 'incoming_quantity', 'outgoing_quantity', 'current_remainder', 'wholesale_price', 'supplier', 'av_price', 'retail_price', 'user', 'inventory_doc', 'for_mp_sale', 'mp_RRP', ) 
    list_filter = ('shop', 'rho_type', 'category', 'supplier',)
    ordering = ('-created',)
    list_per_page=50
    list_select_related = True
    list_editable = ('av_price', 'category', 'name', 'ean', 'supplier')
    search_fields = ('imei',)

    #I don't know how it works, but this functions created a separate column based on column 'created', but with more precise time '19 Feb 2022 15:54:00' instead of  'Feb. 21, 2022, 3:11 p.m.' I deleted 'created' from display_list. Somehow it may influence to filtering, but so far I have not noticed anything.
    def time_seconds(self, obj):
        return obj.created.strftime("%d %b %Y %H:%M:%S.%f")#displays microsecs
        #return obj.created.strftime("%d %b %Y %H:%M:%S")
    time_seconds.admin_order_field = 'created'
    time_seconds.short_description = 'Precise Time'

    # def get_ordering(self, request):
    #     if request.user.is_superuser:
    #         return ('imei', '-created')
    #     else:
    #         return ('imei',)

class RemainderCurrentAdmin(admin.ModelAdmin):
    list_display = ('updated', 'shop', 'name', 'imei', 'current_remainder', 'retail_price', 'category')  
    list_filter = ('shop',)
    search_fields = ('imei', )
  
class AvPriceAdmin(admin.ModelAdmin):
    list_display = ('updated', 'name', 'imei', 'current_remainder')  

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'time_seconds', 'title' , 'user', 'sum', 'client', 'base_doc', 'posted')
    ordering = ('-created',)
    list_editable= ('posted', )
    search_fields = ('id', )
    list_filter = ('title',)
    #I don't know how it works, but this functions created a separate columng based on column 'created', but with more precise time '19 Feb 2022 15:54:00' instead of  'Feb. 21, 2022, 3:11 p.m.' I deleted 'created' from display_list. Somehow it may influence to filtering, but so far I have not noticed anything.
    def time_seconds(self, obj):
        return obj.created.strftime("%d %b %Y %H:%M:%S.%f")#displays microsecs
        #return obj.created.strftime("%d %b %Y %H:%M:%S")
    time_seconds.admin_order_field = 'created'
    time_seconds.short_description = 'Precise Time'

class RegisterAdmin(admin.ModelAdmin):
    list_display = ('created', 'document', 'doc_type', 'product', 'imei', 'sub_total', 'identifier', 'new', 'deleted')
    search_fields = ('imei', )

class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('id', 'created')

class InventoryListAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'doc_type', 'imei', 'product')

#admin.site.register(Delivery, DeliveryAdmin)
#admin.site.register(Recognition, RecognitionAdmin)
#admin.site.register(Sale, SaleAdmin)
#admin.site.register(Transfer, TransferAdmin)
#admin.site.register(SignOff, SignOffAdmin)
#admin.site.register(Returning, ReturningAdmin)
#admin.site.register(Revaluation, RevaluationAdmin)
admin.site.register(RemainderHistory, RemainderHistoryAdmin)
admin.site.register(RemainderCurrent, RemainderCurrentAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Register, RegisterAdmin)
admin.site.register(Identifier, IdentifierAdmin)
admin.site.register(AvPrice, AvPriceAdmin)
admin.site.register(InventoryList, InventoryListAdmin)




