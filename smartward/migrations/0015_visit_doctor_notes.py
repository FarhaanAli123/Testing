# Generated by Django 5.0 on 2024-10-03 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smartward', '0014_alter_visit_options_remove_visit_visit_results_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='doctor_notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]