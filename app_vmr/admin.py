from django.contrib import admin
from . models import VMR_check


class VMR_checkAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'shop', 'user', 'mnp_offer', 'sim_offer', 'rtc_offer', 'mixx_offer', 'client_problem_res',)



admin.site.register(VMR_check, VMR_checkAdmin)