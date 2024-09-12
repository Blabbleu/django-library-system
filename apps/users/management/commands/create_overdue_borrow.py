from django.core.management.base import BaseCommand
from books_db.models import Book, Borrow
from apps.users.models import Reader
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create a borrow record with a past due date to test the fine system.'

    def handle(self, *args, **kwargs):
        # Fetch a book and reader from the database
        book = Book.objects.first()
        reader = Reader.objects.first()

        if not book or not reader:
            self.stdout.write(self.style.ERROR('No book or reader found in the database.'))
            return

        # Create a borrow record with a past due date
        borrow_date = timezone.now() - timedelta(days=10)  # Borrowed 10 days ago
        due_date = borrow_date + timedelta(days=4)  # Due date was 6 days ago

        borrow = Borrow.objects.create(
            book=book,
            borrower=reader,
            borrow_date=borrow_date,
            due_date=due_date
        )

        self.stdout.write(self.style.SUCCESS(f'Borrow record created with ID {borrow.id}'))
