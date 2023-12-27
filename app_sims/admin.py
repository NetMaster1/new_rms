from django.contrib import admin
from . models import SimReturnRecord, SimRegisterRecord, SimSupplierReturnRecord, SimSigningOffRecord

class SimReturnRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'imei', 'name', 'user')

class SimRegisterRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'imei', 'name', 'user')

class SimSupplierReturnRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'imei', 'name', 'user')

class SimSigningOffRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'document', 'imei', 'name', 'user')

admin.site.register(SimReturnRecord, SimReturnRecordAdmin)
admin.site.register(SimRegisterRecord, SimRegisterRecordAdmin)
admin.site.register(SimSupplierReturnRecord, SimSupplierReturnRecordAdmin)
admin.site.register(SimSigningOffRecord, SimSigningOffRecordAdmin)