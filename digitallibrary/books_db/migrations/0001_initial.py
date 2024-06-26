# Generated by Django 5.0.6 on 2024-06-12 03:01

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.CharField(editable=False, max_length=50, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('isbn', models.CharField(max_length=13)),
                ('genre', models.CharField(choices=[('A', 'Genre A'), ('B', 'Genre B'), ('C', 'Genre C')], max_length=1)),
                ('author', models.CharField(max_length=100)),
                ('publication_year', models.PositiveIntegerField()),
                ('publisher', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('page_count', models.PositiveIntegerField(blank=True, null=True)),
                ('categories', models.CharField(blank=True, max_length=255, null=True)),
                ('thumbnail', models.URLField(blank=True, null=True)),
                ('entry_date', models.DateField(default=django.utils.timezone.now)),
                ('value', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('borrowed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Borrow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('borrow_date', models.DateField(default=django.utils.timezone.now)),
                ('due_date', models.DateField()),
                ('return_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled'), ('RETURNED', 'Returned')], default='PENDING', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Fine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fine_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('return_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('collection_date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='LostReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateField(auto_now_add=True)),
                ('fine', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='RemovalReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('removal_date', models.DateField(auto_now_add=True)),
                ('reason', models.CharField(choices=[('L', 'Lost'), ('D', 'Damaged'), ('R', 'Reader Lost')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Return',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('return_date', models.DateField(auto_now_add=True)),
                ('fine_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
        ),
    ]
