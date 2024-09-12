from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from books_db.models import Borrow

class Command(BaseCommand):
    help = 'Cancel and delete borrow requests that have not been confirmed within 2 days of the request date'

    def handle(self, *args, **kwargs):
        two_days_ago = timezone.now() - timedelta(days=2)
        unconfirmed_borrows = Borrow.objects.filter(status='PENDING', request_date__lt=two_days_ago)

        for borrow in unconfirmed_borrows:
            self.stdout.write(f"Canceling and deleting borrow request: {borrow}")
            borrow.delete()

        self.stdout.write(self.style.SUCCESS('Successfully canceled and deleted unconfirmed borrow requests older than 2 days'))
