from django.contrib import admin
from . models import BonusAccount

class BonusAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'smarts', 'phones', 'acces', 'sims', 'modems', 'insurance', 'esset', 'wink', 'service', 'other')

admin.site.register(BonusAccount, BonusAccountAdmin)