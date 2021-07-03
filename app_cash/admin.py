from django.contrib import admin
from . models import Cash, CashRemainder

class CashAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'shop', 'pre_remainder', 'cash_in', 'cash_out', 'current_remainder', 'user')

class CashRemainderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shop', 'remainder')

admin.site.register(Cash, CashAdmin)
admin.site.register(CashRemainder, CashRemainderAdmin)
