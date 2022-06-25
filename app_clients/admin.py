from django.contrib import admin
from . models import Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'l_name', 'created', 'phone', 'bar_code', 'accum_cashback', 'user')

admin.site.register(Customer, CustomerAdmin)