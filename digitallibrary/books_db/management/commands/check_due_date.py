from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from books_db.models import Borrow
from books_db.utils import send_notification_email
from notifications.utils import create_notification

class Command(BaseCommand):
    help = 'Send notifications for books approaching due dates and overdue books.'

    def handle(self, *args, **kwargs):
        now = timezone.now().date()
        three_days = now + timedelta(days=3)
        two_days = now + timedelta(days=2)
        one_day = now + timedelta(days=1)

        borrows = Borrow.objects.filter(
            status='CONFIRMED',
            return_date__isnull=True,
            due_date__in=[three_days, two_days, one_day, now - timedelta(days=1)]
        )

        for borrow in borrows:
            if borrow.due_date == three_days:
                subject = 'Book Due in 3 Days'
            elif borrow.due_date == two_days:
                subject = 'Book Due in 2 Days'
            elif borrow.due_date == one_day:
                subject = 'Book Due Tomorrow'
            elif borrow.due_date == now:
                subject = 'Book Due Today'
            else:
                subject = 'Book Overdue'

            message = f'Dear {borrow.borrower.full_name},\n\nThe book "{borrow.book.title}" is due on {borrow.due_date}. Please return it on time to avoid any fines.'
            recipient_list = [borrow.borrower.email]
            send_notification_email(subject, message, recipient_list)
            create_notification(borrow.borrower, message)

        self.stdout.write(self.style.SUCCESS('Successfully sent notifications'))
