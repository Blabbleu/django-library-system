from django.core.management.base import BaseCommand
from apps.users.models import Reader
from books_db.models import BookList


class Command(BaseCommand):
    help = 'Replace default book lists for existing users'

    def handle(self, *args, **kwargs):
        readers = Reader.objects.all()
        replaced_count = 0

        for reader in readers:
            # Delete existing default lists
            BookList.objects.all().delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully replaced {replaced_count} default book lists.'))