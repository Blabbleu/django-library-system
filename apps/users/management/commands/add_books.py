from django.core.management.base import BaseCommand
from books_db.models import Book
from apps.users.models import CustomUser
import random
import uuid

class Command(BaseCommand):
    help = 'Add books to the database'

    def handle(self, *args, **kwargs):
        genres = ['A', 'B', 'C']
        authors = ['Author One', 'Author Two', 'Author Three']
        publishers = ['Publisher One', 'Publisher Two', 'Publisher Three']
        titles = ['Book One', 'Book Two', 'Book Three']

        # Ensure there's at least one user to assign as receiver
        if not CustomUser.objects.exists():
            self.stdout.write(self.style.ERROR('No users found in the database. Please add at least one user.'))
            return

        receiver = CustomUser.objects.first()

        for _ in range(10):  # Add 10 books
            book = Book(
                id=str(uuid.uuid4()),  # Ensure the ID is a string
                title=random.choice(titles),
                genre=random.choice(genres),
                author=random.choice(authors),
                publication_year=random.randint(2015, 2023),
                publisher=random.choice(publishers),
                value=round(random.uniform(10.00, 100.00), 2),  # Rounded to 2 decimal places
                receiver=receiver,
            )
            book.save()

        self.stdout.write(self.style.SUCCESS('Successfully added books to the database.'))
