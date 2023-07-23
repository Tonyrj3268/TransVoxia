# Generated by Django 4.2.1 on 2023-07-22 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0002_alter_video_file_location'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transcript',
            name='taskID',
        ),
        migrations.RemoveField(
            model_name='video',
            name='taskID',
        ),
        migrations.AddField(
            model_name='transcript',
            name='modified_transcript',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='transcript',
            name='transcript',
            field=models.TextField(blank=True, null=True),
        ),
    ]