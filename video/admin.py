from django.contrib import admin

# Register your models here.
from video.models import *

class Video_Info_Admin(admin.ModelAdmin):
    list_display = ('taskID','file_location','length','upload_time','status')
class Transcript_Admin(admin.ModelAdmin):
    list_display = ('taskID','transcript')
admin.site.register(Video,Video_Info_Admin)
admin.site.register(Transcript,Transcript_Admin)