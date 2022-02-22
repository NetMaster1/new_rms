from django.contrib import admin
from . models import ErrorLog

class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'created', 'definition', 'user',)


admin.site.register(ErrorLog, ErrorLogAdmin)