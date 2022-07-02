from django.contrib import admin
from . models import Tutorial

class TutorialAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'video_file')


admin.site.register(Tutorial, TutorialAdmin)
