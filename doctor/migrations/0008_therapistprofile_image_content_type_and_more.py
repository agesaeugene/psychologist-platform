# Generated by Django 5.1.4 on 2025-01-06 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctor', '0007_appointment_accepted_appointment_accepted_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='therapistprofile',
            name='image_content_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='therapistprofile',
            name='image_filename',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='therapistprofile',
            name='image',
            field=models.BinaryField(blank=True, null=True),
        ),
    ]
