# Generated by Django 5.0 on 2024-08-09 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartward', '0006_appointment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='usertype',
            field=models.CharField(choices=[('doctor', 'Doctor'), ('nurse', 'Nurse'), ('receptionist', 'Receptionist'), ('admin', 'Admin')], max_length=20),
        ),
    ]