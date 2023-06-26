# Generated by Django 3.2.19 on 2023-06-24 15:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('userID', models.AutoField(primary_key=True, serialize=False)),
                ('membership_level', models.CharField(max_length=255)),
                ('expiration_date', models.DateField()),
                ('email', models.EmailField(default='default@example.com', max_length=255, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('fb_id', models.CharField(blank=True, max_length=255)),
                ('google_id', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('taskID', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('fileLocation', models.CharField(default='找不到該檔案', max_length=50)),
                ('request_time', models.DateTimeField(auto_now_add=True)),
                ('target_language', models.CharField(max_length=255)),
                ('voice_selection', models.CharField(choices=[('ko-KR-Standard-A', 'ko-KR-Standard-A'), ('larry', 'larry'), ('zh-TW-YunJheNeural', 'zh-TW-YunJheNeural')], max_length=255)),
                ('mode', models.CharField(choices=[('transcript', '逐字稿'), ('audio', '語音'), ('video', '影片')], max_length=50)),
                ('status', models.CharField(choices=[('0', '未處理'), ('1', '文字稿生成完成'), ('2', 'Deepl翻譯完成'), ('3', 'Play.ht語音生成完成'), ('4', '任務完成'), (None, 'N/A')], max_length=50)),
                ('edit_mode', models.BooleanField(default=False)),
                ('userID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
            ],
        ),
    ]
