from django.contrib import admin
from . models import Cashback

class CashbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'size')

admin.site.register(Cashback, CashbackAdmin)
