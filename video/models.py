from django.db import models

class Video(models.Model):
    url = models.URLField(primary_key=True)
    length = models.IntegerField ()
    upload_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url
class Transcript(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE,db_constraint=False)
    language = models.CharField(max_length=50)
    transcript = models.TextField()
    def __str__(self):
        return f"{self.language} - {self.video.url}"
