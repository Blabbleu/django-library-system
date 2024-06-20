import os
from django.conf import settings
from .models import Notification
from django.core.mail import send_mail
from users.models import CustomUser
from icalendar import Calendar, Event
from datetime import datetime
from django.utils.timezone import localtime
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.core.mail import EmailMessage
import tempfile



def create_notification(subject, user, message, ical_event_details=None):
    Notification.objects.create(
        recipient=user,
        message=message
    )

    ical_file_path = None
    if ical_event_details:
        ical_file_path = generate_ical_event(
            summary=ical_event_details.get('summary'),
            dtstart=ical_event_details.get('dtstart'),
            dtend=ical_event_details.get('dtend'),
            description=ical_event_details.get('description', ''),
            location=ical_event_details.get('location', ''),
            uid=ical_event_details.get('uid', f'{now().timestamp()}@librarysystem.com')
        )

    send_notification_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
        user=user,
        ical_file_path=ical_file_path
    )

def send_notification_email(subject, message, recipient_list, user=None, ical_file_path=None):
    context = {
        'user': user,
        'message': message
    }
    
    email_content = render_to_string('email_templates/notification_email.html', context)
    
    email = EmailMessage(
        subject,
        email_content,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
    )
    email.content_subtype = "html"  # Main content is now HTML

    # Attach iCal file if provided
    if ical_file_path:
        with open(ical_file_path, 'rb') as f:
            email.attach(os.path.basename(ical_file_path), f.read(), 'text/calendar')

    email.send(fail_silently=False)
    
    # Clean up the temporary file
    if ical_file_path:
        os.remove(ical_file_path)

def send_notification_email_to_department(subject, message, department, context=None, template_name=None, ical_file_path=None):
    recipients = CustomUser.objects.filter(department=department).values_list('email', flat=True)
    if template_name:
        html_content = render_to_string(template_name, context)
        email = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
        email.attach_alternative(html_content, "text/html")
    else:
        email = EmailMultiAlternatives(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)

    # Attach iCal file if provided
    if ical_file_path:
        with open(ical_file_path, 'rb') as ical_file:
            email.attach('event.ics', ical_file.read(), 'text/calendar')

    email.send()



def generate_ical_event(summary, dtstart, dtend, description='', location='', uid=''):
    cal = Calendar()
    event = Event()
    
    event.add('summary', summary)
    event.add('dtstart', localtime(dtstart))
    event.add('dtend', localtime(dtend))
    event.add('dtstamp', datetime.now())
    event.add('description', description)
    event.add('location', location)
    event['uid'] = uid or f'{dtstart.timestamp()}@librarysystem.com'  # Ensure uniqueness if UID is not provided

    cal.add_component(event)
    
    # Create a temporary file to store the iCal data
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ics', mode='wb') as temp_file:
        temp_file.write(cal.to_ical())
        temp_file_path = temp_file.name
    
    return temp_file_path