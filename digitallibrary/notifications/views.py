from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.shortcuts import redirect
from django.http import JsonResponse

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})

@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.read = True
    notification.save()
    return redirect('notification_list')

from django.core.mail import send_mail
from django.conf import settings
import datetime
from books_db.models import Borrow

def send_notification(borrow, notification_type):
    subject = ''
    message = ''
    recipient_list = [borrow.borrower.email]
    
    if notification_type == "overdue":
        subject = f'Overdue Notice: {borrow.book.title}'
        message = f'Your borrowed book "{borrow.book.title}" is overdue. Please return it as soon as possible.'
    elif notification_type == "approaching":
        days_left = (borrow.due_date - datetime.date.today()).days
        subject = f'Return Reminder: {borrow.book.title}'
        message = f'Your borrowed book "{borrow.book.title}" is due in {days_left} day(s). Please return it on time.'
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

@login_required
def check_unread_notifications(request):
    unread_count = Notification.objects.filter(recipient=request.user, read=False).count()
    return JsonResponse({'unread_count': unread_count})
