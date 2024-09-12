# books_db/tasks.py

from celery import shared_task
from django.utils import timezone
from apps.books_db.models import Borrow
from apps.notifications.utils import create_notification

@shared_task
def check_due_dates():
    now = timezone.now().date()
    upcoming_thresholds = [1, 2, 3]  # days before due date
    borrows = Borrow.objects.filter(status='CONFIRMED')

    for borrow in borrows:
        due_in_days = (borrow.due_date - now).days

        if due_in_days < 0:
            subject = 'Overdue Book borrow at MT Library'
            message = f"Dear {borrow.borrower.user.username},\nYour borrowed book {borrow.book.title} is overdue. Please return it as soon as possible.\nReminder: A surcharge of 2 dollars a day will be accounted for every day you are late.\nThank you for your time.\nBest regards, MT Library."
            create_notification(subject, borrow.borrower.user, message)
        elif due_in_days in upcoming_thresholds:
            subject = 'Upcoming Due Date for Borrowed Book at MT Library'
            message = f"Dear {borrow.borrower.user.username},\nYour borrowed book {borrow.book.title} is due in {due_in_days} day(s).\nReminder: A surcharge of 2 dollars a day will be accounted for every day you are late.\nThank you for your time.\nBest regards, MT Library."
            create_notification(subject, borrow.borrower.user, message)

@shared_task
def add(x, y):
    return x + y
