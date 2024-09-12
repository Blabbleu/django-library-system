from django.core.management.base import BaseCommand
from apps.users.models import Reader
from books_db.models import BookList

class Command(BaseCommand):
    help = 'Create default book lists for existing users'

    def handle(self, *args, **kwargs):
        readers = Reader.objects.all()
        created_count = 0

        for reader in readers:
            # Delete old lists
            BookList.objects.filter(user=reader, ready_made=True).delete()

            # Create new lists with correct slugs
            _, created = BookList.objects.get_or_create(user=reader, name='Favorites', slug='favorites', ready_made=True)
            if created:
                created_count += 1
            _, created = BookList.objects.get_or_create(user=reader, name='Read Later', slug='read-later', ready_made=True)
            if created:
                created_count += 1
            _, created = BookList.objects.get_or_create(user=reader, name='Read', slug='read', ready_made=True)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} default book lists.'))