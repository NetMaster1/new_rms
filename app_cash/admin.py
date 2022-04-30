from django.contrib import admin
from . models import Cash, Credit, Card, PaymentRegister #CashRemainder

class CashAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'time_seconds', 'document', 'cho_type', 'shop', 'pre_remainder', 'cash_in', 'cash_out', 'current_remainder', 'cash_off_reason', 'cash_in_reason', 'cash_receiver')
    ordering = ('-created',)
    list_filter = ('shop',)
    list_per_page=25
    list_select_related = True

    #I don't know how it works, but this functions created a separate column based on column 'created', but with more precise time '19 Feb 2022 15:54:00' instead of  'Feb. 21, 2022, 3:11 p.m.' I deleted 'created' from display_list. Somehow it may influence to filtering, but so far I have not noticed anything.
    def time_seconds(self, obj):
        return obj.created.strftime("%d %b %Y %H:%M:%S.%f")#displays microsecs
        #return obj.created.strftime("%d %b %Y %H:%M:%S")
    time_seconds.admin_order_field = 'created'
    time_seconds.short_description = 'Precise Time'


class CreditAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'sum', 'user')
    ordering = ('-created',)
    list_filter = ('shop',)
    list_per_page=25

class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'sum', 'user')
    ordering = ('-created',)
    list_filter = ('shop',)
    list_per_page=25

class PaymentRegisterAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'cash', 'card', 'credit')

admin.site.register(Cash, CashAdmin)
#admin.site.register(CashRemainder, CashRemainderAdmin)
admin.site.register(Credit, CreditAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(PaymentRegister, PaymentRegisterAdmin)