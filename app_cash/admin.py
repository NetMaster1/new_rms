from django.contrib import admin
from . models import Cash, CashRemainder, Credit, Card

class CashAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created', 'document', 'cho_type', 'shop', 'pre_remainder', 'cash_in', 'cash_out', 'current_remainder', 'cash_off_reason', 'cash_in_reason', 'cash_receiver')
    ordering = ('-created',)

class CashRemainderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'remainder')

class CreditAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'sum', 'user')

class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'sum', 'user')

# class PaymentRegisterAdmin(admin.ModelAdmin):
#     list_display = ('id', 'created', 'document', 'cash', 'card', 'credit')

admin.site.register(Cash, CashAdmin)
admin.site.register(CashRemainder, CashRemainderAdmin)
admin.site.register(Credit, CreditAdmin)
admin.site.register(Card, CardAdmin)