from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import django.utils.timezone as timezone
import logging
logger = logging.getLogger(__name__)

class CustomUser(AbstractUser):
    LEVEL_OF_EDUCATION_CHOICES = [
        ('HS', 'High School Diploma'),
        ('IN', 'Intermediate Level'),
        ('AD', 'Associate Degree'),
        ('BA', 'Bachelor\'s Degree'),
        ('MA', 'Master\'s Degree'),
        ('PH', 'Doctorate'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('LI', 'Librarian'),
        ('WK', 'Warehouse Keeper'),
        ('TR', 'Treasurer'),
        ('BD', 'Board of Directors'),
        ('IT', 'IT department'),
    ]
    
    POSITION_CHOICES = [
        ('DI', 'Director'),
        ('DD', 'Deputy Director'),
        ('DH', 'Department Head'),
        ('DDH', 'Deputy Department Head'),
        ('SM', 'Staff Member'),
        ('ITT', 'IT Technician')
    ]
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    level_of_education = models.CharField(max_length=2, choices=LEVEL_OF_EDUCATION_CHOICES, null=True, blank=True)
    department = models.CharField(max_length=2, choices=DEPARTMENT_CHOICES, null=True, blank=True)
    position = models.CharField(max_length=3, choices=POSITION_CHOICES, null=True, blank=True)
    

    @property
    def is_reader(self):
        return self.department is None or self.position is None
    
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.is_staff = True
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Reader(models.Model):
    READER_TYPE_CHOICES = [
        ('X', 'Type X'),
        ('Y', 'Type Y'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='reader_profile')
    date_of_birth = models.DateField()
    address = models.TextField()
    date_of_card_creation = models.DateField(default=timezone.now)
    reader_type = models.CharField(max_length=1, choices=READER_TYPE_CHOICES)
    borrowed_books = models.ManyToManyField('books_db.Borrow', related_name='borrowed_books', blank=True)
    owed_money = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def active_borrows(self):
        return self.borrowed_books.filter(return_date__isnull=True, borrower=self, status='CONFIRMED')

    def clean(self):
        if self.date_of_birth is None:
            logger.error(f'Date of birth is None for reader: {self.user.username}')
            raise ValidationError('Date of birth cannot be null.')
        logger.info(f'Date of birth for reader {self.user.username}: {self.date_of_birth}')
        age = (timezone.now().date() - self.date_of_birth).days // 365
        if age < 18 or age > 55:
            raise ValidationError('Reader must be between 18 and 55 years old.')
    
    def card_expiry_date(self):
        return self.date_of_card_creation + timedelta(days=180)
    
    def __str__(self):
        return self.user.username
