# Generated by Django 4.2.1 on 2023-07-22 07:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0003_remove_transcript_taskid_remove_video_taskid_and_more'),
        ('core', '0006_alter_task_voice_selection'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='transcript',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='video.transcript'),
        ),
        migrations.AddField(
            model_name='task',
            name='video',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='video.video'),
        ),
    ]
