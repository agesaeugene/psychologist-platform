# Generated by Django 5.1.4 on 2025-01-03 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctor', '0005_alter_appointment_options_appointment_accepted_date_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='appointment',
            options={},
        ),
        migrations.RemoveField(
            model_name='appointment',
            name='accepted',
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
            name='meet_link',
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
            model_name='therapistprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='therapistprofile',
            name='username',
            field=models.CharField(max_length=100),
        ),
    ]
