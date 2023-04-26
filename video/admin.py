from django.contrib import admin

# Register your models here.
from video.models import *

class Video_Info_Admin(admin.ModelAdmin):
    list_display = ('url','length','upload_time')
class Transcript_Admin(admin.ModelAdmin):
    list_display = ('video','language','transcript')
admin.site.register(Video,Video_Info_Admin)
admin.site.register(Transcript,Transcript_Admin)