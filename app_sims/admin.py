from django.contrib import admin
from . models import SimReturnRecord, SimRegisterRecord

class SimReturnRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'imei', 'name', 'user')

class SimRegisterRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'imei', 'name', 'user')

admin.site.register(SimReturnRecord, SimReturnRecordAdmin)
admin.site.register(SimRegisterRecord, SimRegisterRecordAdmin)