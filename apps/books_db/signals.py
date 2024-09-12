from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Borrow, Return, Fine, LostReport, BookList
from django.core.exceptions import ValidationError


@receiver(post_save, sender=Borrow)
def add_to_read_list(sender, instance, **kwargs):
    if instance.status == 'RETURNED':
        read_list, created = BookList.objects.get_or_create(
            user=instance.borrower,
            slug='read',
            defaults={'name': 'Read', 'ready_made': True}
        )
        read_list.books.add(instance.book)


@receiver(post_save, sender=Borrow)
def update_borrow_status(sender, instance, created, **kwargs):
    """Signal to update book status and borrower's borrowed books."""
    if created:
        if instance.status == 'CONFIRMED':
            instance.book.borrowed = True
            instance.borrower.borrowed_books.add(instance)
        elif instance.status in ['CANCELLED', 'RETURNED']:
            instance.book.borrowed = False
            instance.return_date = timezone.now()
            instance.borrower.borrowed_books.remove(instance)
        instance.book.save()
        instance.borrower.save()


# @receiver(pre_save, sender=Return)
# def calculate_return_fine(sender, instance, **kwargs):
#     """Signal to calculate fine and update credit score on return."""
#     if instance.return_date > instance.borrow.due_date:
#         days_overdue = (instance.return_date - instance.borrow.due_date).days
#         instance.fine_amount = days_overdue * 2  # Fine of $2 per day overdue
#         if days_overdue >= 5:
#             instance.reader.credit_score -= days_overdue  # Deduct credit score by the number of days overdue
#         instance.reader.owed_money += instance.fine_amount
#         instance.reader.save()
#     if instance.return_date <= instance.borrow.due_date:
#         instance.reader.credit_score += 1  # Add 1 credit score for returning a book on time
#     instance.reader.borrowed_books.remove(instance.borrow)
#     instance.borrow.book.borrowed = False
#     instance.borrow.status = 'RETURNED'
#     instance.borrow.book.save()
#
#     # Add the book to the "Read" list
#     read_list, _ = BookList.objects.get_or_create(
#         user=instance.reader, slug='read', defaults={'name': 'Read', 'ready_made': True}
#     )
#     read_list.books.add(instance.borrow.book)
#
#     instance.borrow.save()
#     instance.reader.save()


@receiver(post_save, sender=Fine)
def update_fine_status(sender, instance, created, **kwargs):
    """Signal to update reader's owed money on fine collection."""
    if created:
        if instance.return_amount > instance.reader.owed_money:
            raise ValidationError('Return amount cannot exceed the previous dues.')
        instance.reader.owed_money -= instance.return_amount
        instance.reader.save()


@receiver(post_save, sender=LostReport)
def handle_lost_report(sender, instance, created, **kwargs):
    """Signal to handle lost report fines and credit score."""
    if created:
        instance.fine = instance.book.value
        instance.reporter.owed_money += instance.fine
        instance.reporter.credit_score -= 2  # Deduct 2 credit score for losing a book
        instance.reporter.save()