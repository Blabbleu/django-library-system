# Generated by Django 5.0.6 on 2024-06-12 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books_db', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='genre',
            field=models.CharField(choices=[('A', 'Genre A'), ('B', 'Genre B'), ('C', 'Genre C')], default='A', max_length=1),
        ),
    ]
