from django.contrib import admin
from . models import SimReturnRecord

class SimReturnRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'imei', 'name', 'user')

admin.site.register(SimReturnRecord, SimReturnRecordAdmin)