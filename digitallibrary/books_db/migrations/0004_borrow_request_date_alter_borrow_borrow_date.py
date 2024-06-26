# Generated by Django 5.0.6 on 2024-06-12 07:43

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books_db', '0003_alter_book_genre'),
    ]

    operations = [
        migrations.AddField(
            model_name='borrow',
            name='request_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='borrow',
            name='borrow_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
