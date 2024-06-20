import uuid
import requests

def generate_book_id(genre):
    """
    Generate a unique book ID starting with the genre.
    """
    return f"{genre}-{uuid.uuid4()}"
from django.core.mail import send_mail
from django.conf import settings

def send_notification_email(subject, message, recipient_list):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
    )


def get_book_details_from_google_books(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data:
            book_info = data['items'][0]['volumeInfo']
            published_date = book_info.get('publishedDate', '')
            publication_year = ''
            if published_date:
                publication_year = published_date.split('-')[0]  # Extract the year part only

            return {
                'title': book_info.get('title', ''),
                'isbn': isbn,
                'author': ', '.join(book_info.get('authors', [])),
                'publisher': book_info.get('publisher', ''),
                'publication_year': publication_year,
                'description': book_info.get('description', ''),
                'page_count': book_info.get('pageCount', 0),
                'categories': ', '.join(book_info.get('categories', [])),
                'thumbnail': book_info['imageLinks']['thumbnail'] if 'imageLinks' in book_info else '',
                'value':12,
            }
    return None


