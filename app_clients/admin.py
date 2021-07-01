from django.contrib import admin
from . models import Client

class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'f_name','l_name', 'created', 'phone', 'bar_code', 'accum_cashback')

admin.site.register(Client, ClientAdmin)