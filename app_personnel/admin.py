from django.contrib import admin
from . models import BonusAccount, BulkSimMotivation

class BonusAccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'smarts', 'phones', 'acces', 'sims', 'modems', 'insurance', 'esset', 'wink', 'service', 'other')

class BulkSimMotivationAdmin(admin.ModelAdmin):
    list_display = ('id', 'sim_price', 'bonus_per_sim')

admin.site.register(BonusAccount, BonusAccountAdmin)
admin.site.register(BulkSimMotivation, BulkSimMotivationAdmin)