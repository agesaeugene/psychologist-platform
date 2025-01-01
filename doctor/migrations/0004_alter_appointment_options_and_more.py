# Generated by Django 5.1.4 on 2025-01-01 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctor', '0003_therapistprofile_alter_appointment_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appointment',
            options={},
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='accepted_date',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='email',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='request',
        ),
        migrations.AlterField(
            model_name='appointment',
            name='meet_link',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
