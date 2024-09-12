import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from apps.users.models import CustomUser, Reader
from apps.books_db import utils
from django.core.exceptions import ValidationError
from datetime import datetime

class ActiveBorrowManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(return_date__isnull=True, status='CONFIRMED')


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if hasattr(self, 'clean') and callable(self.clean):
            self.clean()
        super().save(*args, **kwargs)


class Book(BaseModel):
    GENRE_CHOICES = [('A', 'Genre A'), ('B', 'Genre B'), ('C', 'Genre C')]
    title = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13)
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES, default='A')
    language = models.CharField(max_length=50, default='English')
    author = models.CharField(max_length=100)
    publication_year = models.PositiveIntegerField()
    publisher = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    page_count = models.PositiveIntegerField(blank=True, null=True)
    categories = models.CharField(max_length=255, null=True, blank=True)
    thumbnail = models.URLField(null=True, blank=True)
    entry_date = models.DateField(default=timezone.now, editable=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=12)
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department__in': ['WK', 'IT']})
    borrowed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = utils.generate_book_id(self.genre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class BookList(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    user = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='book_lists')
    books = models.ManyToManyField(Book, related_name='book_lists')
    ready_made = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'slug')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Borrow(BaseModel):
    STATUS_CHOICES = [('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled'), ('RETURNED', 'Returned')]
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
            self.book.borrowed = True
            self.book.save()
        super().save(*args, **kwargs)

    def clean(self):

        overdue_books = Borrow.objects.filter(borrower=self.borrower, return_date__isnull=True, due_date__lt=timezone.now().date())
        if overdue_books.exists():
            raise ValidationError('Borrower has overdue books.')

        active_borrows = Borrow.objects.filter(borrower=self.borrower, return_date__isnull=True, status='CONFIRMED').count()
        if active_borrows >= 5:
            raise ValidationError('Borrower has already borrowed the maximum number of books (5).')

    def __str__(self):
        return f"{self.book.title} borrowed by {self.borrower.user.username}"


class Return(BaseModel):
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE)
    borrow = models.ForeignKey(Borrow, on_delete=models.CASCADE)
    return_date = models.DateField(auto_now_add=True)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Ensure return_date is set if not already
        if self.return_date is None:
            self.return_date = timezone.now().date()

        # Set the borrow's return_date
        self.borrow.return_date = self.return_date

        if isinstance(self.borrow.due_date, datetime):
            due_date = self.borrow.due_date.date()
        else:
            due_date = self.borrow.due_date

        # Calculate fine if return_date is after due_date
        if self.return_date > due_date:
            days_overdue = (self.return_date - due_date).days
            self.fine_amount = days_overdue * 2  # Fine of $2 per day overdue
            self.reader.credit_score -= days_overdue - 1  # Deduct credit score by the number of days overdue
            self.reader.owed_money += self.fine_amount
            self.reader.save()
        else:
            self.reader.credit_score += 1  # Add 1 credit score for returning a book on time

        # Remove the borrow instance from the reader's borrowed books
        self.reader.borrowed_books.remove(self.borrow)

        # Update the book's borrowed status
        self.borrow.book.borrowed = False
        self.borrow.book.save()

        # Update the borrow's status
        self.borrow.status = 'RETURNED'
        self.borrow.save()

        # Save the reader instance
        self.reader.save()

        # Save the return instance
        super().save(*args, **kwargs)


    @property
    def previous_dues(self):
        return self.reader.owed_money - self.fine_amount

    @property
    def total_dues(self):
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


class Fine(BaseModel):
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


class LostReport(BaseModel):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reporter = models.ForeignKey(Reader, on_delete=models.CASCADE)
    report_date = models.DateField(auto_now_add=True)
    fine = models.FloatField(default=0)
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department__in': ['LI', 'IT']})

    def save(self, *args, **kwargs):
        self.fine = self.book.value
        self.reporter.owed_money += self.fine
        self.reporter.credit_score -= 2
        self.reporter.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lost report for {self.book.title} by {self.reporter.user.username}"


class RemovalReport(BaseModel):
    REMOVAL_REASON_CHOICES = [('L', 'Lost'), ('D', 'Damaged'), ('R', 'Reader Lost')]
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    remover = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'department': 'WK'})
    removal_date = models.DateField(auto_now_add=True)
    reason = models.CharField(max_length=1, choices=REMOVAL_REASON_CHOICES)

    def __str__(self):
        return f"Removal report for {self.book.title} by {self.remover.username} on {self.removal_date}"
