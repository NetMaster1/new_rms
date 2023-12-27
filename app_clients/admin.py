from django.contrib import admin
from . models import Customer

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'f_name', 'l_name', 'created', 'phone', 'bar_code', 'accum_cashback', 'user')
    list_filter = ('user',)
    #ordering = ('l_name',)
    ordering = ('-id',)
    list_per_page=100
    search_fields = ('phone', )

admin.site.register(Customer, CustomerAdmin)

