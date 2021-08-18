from django.contrib import admin
from . models import Cash, CashRemainder, Credit, Card

class CashAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'pre_remainder', 'cash_in', 'cash_out', 'current_remainder', 'user')
    ordering = ('-created',)

class CashRemainderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'remainder')

class CreditAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'sum', 'user')

class CardAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'shop', 'sum', 'user')

admin.site.register(Cash, CashAdmin)
admin.site.register(CashRemainder, CashRemainderAdmin)
admin.site.register(Credit, CreditAdmin)
admin.site.register(Card, CardAdmin)
