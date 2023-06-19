from django.db import models


class User(models.Model):
    userID = models.AutoField(primary_key=True)
    membership_level = models.CharField(max_length=255)
    expiration_date = models.DateField()
    email = models.EmailField(
        max_length=255, unique=True, default="default@example.com"
    )
    password = models.CharField(max_length=255)
    fb_id = models.CharField(max_length=255, blank=True)
    google_id = models.CharField(max_length=255, blank=True)


class Task(models.Model):
    taskID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    fileLocation = models.CharField(max_length=50, default="找不到該檔案")
    request_time = models.DateTimeField(auto_now_add=True)
    target_language = models.CharField(max_length=255)
    # make a list with tuples and contains these languages with key and same value， ["ko-KR-Standard-A", "larry", "zh-TW-YunJheNeural"]
    voice_CHOICES = [
        ("ko-KR-Standard-A", "ko-KR-Standard-A"),
        ("larry", "larry"),
        ("zh-TW-YunJheNeural", "zh-TW-YunJheNeural"),
    ]
    voice_selection = models.CharField(choices=voice_CHOICES, max_length=255)

    MODE_CHOICES = [("transcript", "逐字稿"), ("audio", "語音"), ("video", "影片")]
    mode = models.CharField(choices=MODE_CHOICES, max_length=50)
    STATUS_CHOICES = [
        ("0", "未處理"),
        ("1", "文字稿生成完成"),
        ("2", "Deepl翻譯完成"),
        ("3", "Play.ht語音生成完成"),
        ("4", "Status 4"),
        (None, "N/A"),
    ]
    status = models.CharField(choices=STATUS_CHOICES, max_length=50)
    edit_mode = models.BooleanField(default=False)
