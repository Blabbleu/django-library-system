from django.db import models
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from users.models import CustomUser, Reader
from .utils import generate_book_id
import django.utils.timezone as timezone

class ActiveBorrowManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(return_date__isnull=True, status = 'CONFIRMED')

class Book(models.Model):
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    GENRE_CHOICES = [
        ('A', 'Genre A'),
        ('B', 'Genre B'),
        ('C', 'Genre C'),
    ]
    
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13)
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES, default='A')
    author = models.CharField(max_length=100)
    publication_year = models.PositiveIntegerField()
    publisher = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    page_count = models.PositiveIntegerField(blank=True, null=True)
    categories = models.CharField(max_length=255, null=True, blank=True)
    thumbnail = models.URLField(null=True, blank=True)
    entry_date = models.DateField(default=timezone.now, editable = True)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department__in': ['WK', 'IT']})
    borrowed = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.id = generate_book_id(self.genre)
        super().save(*args, **kwargs)

    
    def __str__(self):
        return self.title

class Borrow(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrower = models.ForeignKey(Reader, on_delete=models.CASCADE)
    request_date = models.DateTimeField(default=timezone.now)
    borrow_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    objects = models.Manager()  # The default manager.
    active_borrows = ActiveBorrowManager()  # The custom manager.

    def save(self, *args, **kwargs):
        if self.status == 'CONFIRMED' and not self.borrow_date:
            self.borrow_date = timezone.now()
            self.due_date = self.borrow_date + timedelta(days=4)  # Borrowing period of 4 days
        super().save(*args, **kwargs)

        
        # Update book status and borrower's borrowed_books
        if self.status == 'CONFIRMED' and not self.return_date:
            self.book.borrowed = True
            self.borrower.borrowed_books.add(self)
        elif self.status in ['CANCELLED', 'RETURNED']:
            self.book.borrowed = False
            self.return_date = timezone.now()
            self.borrower.borrowed_books.remove(self)
        elif self.status == 'RETURNED':
            self.book.borrowed = False
            self.return_date = timezone.now()
            self.borrower.borrowed_books.remove(self)
        elif self.status == 'PENDING':
            self.book.borrowed = False
            self.borrower.borrowed_books.remove(self)

        self.book.save()
        self.borrower.save()



    def clean(self):
        # Ensure the borrower's card is valid
        if self.borrower.card_expiry_date() < datetime.now().date():
            raise ValidationError('Borrower\'s card is expired.')
        
        # Ensure the borrower has no overdue books
        overdue_books = Borrow.objects.filter(borrower=self.borrower, return_date__isnull=True, due_date__lt=timezone.now().date())
        if overdue_books.exists():
            raise ValidationError('Borrower has overdue books.')

        # Ensure the borrower does not exceed the borrowing limit
        active_borrows = Borrow.objects.filter(borrower=self.borrower, return_date__isnull=True, status = 'CONFIRMED').count()
        if active_borrows >= 5:
            raise ValidationError('Borrower has already borrowed the maximum number of books (5).')

    def __str__(self):
        return f"{self.book.title} borrowed by {self.borrower.user.username}"


class Return(models.Model):
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE)
    borrow = models.ForeignKey('Borrow', on_delete=models.CASCADE)
    return_date = models.DateField(auto_now_add=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Ensure return_date is set if not already
        if self.return_date is None:
            self.return_date = timezone.now().date()

        # Set the borrow's return_date
        self.borrow.return_date = self.return_date

        # Calculate fine if return_date is after due_date
        if self.return_date > self.borrow.due_date:
            days_overdue = (self.return_date - self.borrow.due_date).days
            self.fine_amount = days_overdue * 2  # Fine of $2 per day overdue
            if days_overdue >= 5:
                self.reader.credit_score -= days_overdue  # Deduct credit score by the number of days overdue
            self.reader.owed_money += self.fine_amount
            self.reader.save()

        if self.return_date <= self.borrow.due_date:
            self.reader.credit_score += 1  # Add 1 credit score for returning a book on time

        # Remove the borrow instance from the reader's borrowed books
        self.reader.borrowed_books.remove(self.borrow)

        # Update the book's borrowed status
        self.borrow.book.borrowed = False
        self.borrow.status = 'RETURNED'
        self.borrow.book.save()

        # Save the borrow instance and reader instance
        self.borrow.save()
        self.reader.save()

        # Save the return instance
        super().save(*args, **kwargs)

    @property
    def previous_dues(self):
        # Calculate previous dues before the current fine is added
        return self.reader.owed_money - self.fine_amount

    @property
    def total_dues(self):
        # Total dues after the current fine is added
        return self.reader.owed_money
    
    @property
    def days_borrowed(self):
        borrow_date = self.borrow.borrow_date.date() if isinstance(self.borrow.borrow_date, datetime) else self.borrow.borrow_date
        return (self.return_date - borrow_date).days
    
    @property
    def days_overdued(self):
        if self.return_date > self.borrow.due_date:
            return (self.return_date - self.borrow.due_date).days
        return 0

    def __str__(self):
        return f"{self.borrow.book.title} returned by {self.borrow.borrower.user.username}"

class Fine(models.Model):
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    return_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    collector = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department__in': ['TR', 'IT']})
    collection_date = models.DateField(auto_now_add=True)
    
    @property
    def previous_dues(self):
        return self.reader.owed_money
    
    @property
    def present_dues(self):
        return self.previous_dues - self.return_amount

    def save(self, *args, **kwargs):
        if self.return_amount > self.previous_dues:
            raise ValidationError('Return amount cannot exceed the previous dues.')
        
        self.reader.owed_money -= self.return_amount
        self.reader.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Fine collected from {self.reader.user.username} by {self.collector.username}"

class LostReport(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reporter = models.ForeignKey(Reader, on_delete=models.CASCADE)
    report_date = models.DateField(auto_now_add=True)
    fine = models.FloatField(default=0)
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department__in': ['LI', 'IT']})
    
    def save(self, *args, **kwargs):
        self.fine = self.book.value
        self.reporter.owed_money += self.fine
        self.reporter.credit_score -= 2  # Deduct 2 credit score for losing a book
        self.reporter.save()
        super().save(*args, **kwargs)

class RemovalReport(models.Model):
    REMOVAL_REASON_CHOICES = [
        ('L', 'Lost'),
        ('D', 'Damaged'),
        ('R', 'Reader Lost'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    remover = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department': 'WK'})
    removal_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=1, choices=REMOVAL_REASON_CHOICES)
    
    def __str__(self):
        return f"Removal report for {self.book.title} by {self.remover.username} on {self.removal_date}"