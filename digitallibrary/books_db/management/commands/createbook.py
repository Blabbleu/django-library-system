from django.core.management.base import BaseCommand, CommandError
from books_db.models import Book
from users.models import CustomUser  # Adjust the import according to your user model location

class Command(BaseCommand):
    help = 'Create a new book record'

    def add_arguments(self, parser):
        parser.add_argument('title', type=str, help='The title of the book')
        parser.add_argument('genre', type=str, choices=['A', 'B', 'C'], help='The genre of the book')
        parser.add_argument('author', type=str, help='The author of the book')
        parser.add_argument('publication_year', type=int, help='The publication year of the book')
        parser.add_argument('publisher', type=str, help='The publisher of the book')
        parser.add_argument('value', type=float, help='The value of the book')
        parser.add_argument('receiver_username', type=str, help='The username of the staff receiving the book')

    def handle(self, *args, **kwargs):
        title = kwargs['title']
        genre = kwargs['genre']
        author = kwargs['author']
        publication_year = kwargs['publication_year']
        publisher = kwargs['publisher']
        value = kwargs['value']
        receiver_username = kwargs['receiver_username']

        try:
            receiver = CustomUser.objects.get(username=receiver_username)
        except CustomUser.DoesNotExist:
            raise CommandError('Receiver user does not exist')

        book = Book(
            title=title,
            genre=genre,
            author=author,
            publication_year=publication_year,
            publisher=publisher,
            value=value,
            receiver=receiver
        )

        book.save()
        self.stdout.write(self.style.SUCCESS(f'Successfully created book with ID {book.id}'))

