from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from .models import Book, Borrow, Return, Fine
from .forms import *
from users.models import Reader
from django.core.exceptions import ValidationError
import logging
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from django.db.models import Count, Sum
from .decorators import *
from notifications.utils import *
from django.core.exceptions import ObjectDoesNotExist
from .utils import *
from django.contrib import messages

from notifications.models import Notification
logger = logging.getLogger(__name__)

def create_notifications_for_all_users(subject, message):
    users = CustomUser.objects.all()
    for user in users:
        create_notification(subject, user, message)
        


@login_required
def index(request):
    user_department = request.user.department if request.user.is_authenticated else None
    context = {
        'user_department': user_department,
    }
    return render(request, 'books_db/index.html', context)


@login_required
@department_required(['WK', 'IT'])
def new_book(request):
    isbn_form = ISBNForm()
    form = BookRegForm()
    
    if request.method == 'POST':
        if 'isbn_search' in request.POST:
            isbn_form = ISBNForm(request.POST)
            if isbn_form.is_valid():
                isbn = isbn_form.cleaned_data['isbn']
                book_details = get_book_details_from_google_books(isbn)
                if book_details:
                    form = BookRegForm(initial=book_details)
                else:
                    messages.error(request, "Book details could not be retrieved from Google Books API.")
            else:
                form = BookRegForm()
        else:
            form = BookRegForm(request.POST)
            if form.is_valid():
                book = form.save(commit=False)
                book.receiver = request.user
                book.save()
                messages.success(request, "Book registered successfully.")
                return redirect('/new_book')
            else:
                messages.error(request, "There was an error with the book registration form. Please check the details.")
    
    books = Book.objects.all()
    return render(request, 'books_db/new_book.html', {'isbn_form': isbn_form, 'form': form, 'books': books})

@login_required
def borrow_books(request):
    if request.method == 'POST':
        form = BorrowForm(request.POST)
        if form.is_valid():
            borrow = form.save()
            message = f'{borrow.borrower.user.username} sent a request to borrow "{borrow.book.title}".'
            create_notifications_for_all_users(message)
            return redirect('/borrow')  # Redirect to the same page to clear the form
    else:
        form = BorrowForm()

    borrows = Borrow.objects.filter(return_date__isnull=True)  # Get active borrows
    return render(request, 'books_db/borrow_books.html', {'form': form, 'borrows': borrows})

@login_required
def borrow_books_reader(request):
    if request.method == 'POST':
        form = ReaderBorrowForm(request.POST, user=request.user)
        if form.is_valid():
            borrow = form.save(commit=False)
            try:
                borrow.borrower = request.user.reader_profile
                borrow.status = 'PENDING'  # Initial status when request is made
                borrow.save()
                subject = f'New Book Borrowing Request from {request.user.username}'
                message_body = f'You sent a request to borrow "{borrow.book.title}".'

                # Details for iCal event
                ical_event_details = {
                    'summary': f'Borrowed: {borrow.book.title}',
                    'dtstart': borrow.request_date,
                    'dtend': borrow.request_date,  # Assuming 4 days borrow period
                    'description': f'Book: {borrow.book.title}\nBorrower: {borrow.borrower.user.username}',
                    'location': 'Library Address',  # Customize as needed
                    'uid': f'{borrow.id}@librarysystem.com'
                }

                create_notification(subject, request.user, message_body, ical_event_details=ical_event_details)

                # Send email notification to the LI department
                send_notification_email_to_department(
                    subject='New Book Borrow Request',
                    message=message_body,
                    department='IT'
                )


                return redirect('/readers/borrow')
            except ObjectDoesNotExist:
                form.add_error(None, 'Reader profile not found for the current user.')
    else:
        form = ReaderBorrowForm(user=request.user)

    query = request.GET.get('q', '')
    books = Book.objects.filter(
        Q(title__icontains=query) |
        Q(author__icontains=query),
        borrowed=False
    )

    # Prepare a list of book IDs that the user has already requested
    user_borrow_requests = Borrow.objects.filter(borrower=request.user.reader_profile, status__in=['PENDING', 'CONFIRMED'])
    requested_books = user_borrow_requests.values_list('book_id', flat=True)
    
    return render(request, 'books_db/borrow_books_reader.html', {
        'form': form,
        'books': books,
        'requested_books': requested_books
    })


@login_required
@department_required(['LI', 'IT'])
def confirm_borrow_request(request, borrow_id):
    borrow = get_object_or_404(Borrow, pk=borrow_id)
    borrow.status = 'CONFIRMED'
    borrow.book.borrowed = True
    borrow.save()
    borrow.book.save()


    subject = f'Borrow Request for "{borrow.book.title}" Approved'
    message_body = f'{request.user} approved {borrow.borrower.user.username}\'s borrow request for "{borrow.book.title}",\nYou have picked up "{borrow.book.title}" plese return the book on the right date: {borrow.due_date}.'
    
    borrow_date = timezone.make_aware(datetime.combine(borrow.borrow_date.date(), datetime.min.time()), timezone.get_current_timezone())
    due_date = timezone.make_aware(datetime.combine(borrow.due_date, datetime.min.time()), timezone.get_current_timezone())
    
    ical_event_details = {
                    'summary': f'Picked up: {borrow.book.title}',
                    'dtstart': borrow_date,
                    'dtend': due_date,  # Assuming 4 days borrow period
                    'description': f'Reader: {borrow.borrower.user.username}\n Pick up time: {borrow.borrow_date} \n Borrowing period: 4 days\n Due date: {borrow.due_date}',
                    'location': 'Library Address',  # Customize as needed
                    'uid': f'{borrow.id}@librarysystem.com'
                }
    create_notification(subject, borrow.borrower.user, message_body, ical_event_details=ical_event_details)
    return redirect('borrow_book')

@login_required
@department_required(['LI', 'IT'])
def cancel_borrow_request(request, borrow_id):
    borrow = get_object_or_404(Borrow, pk=borrow_id)
    borrow.status = 'CANCELLED'
    borrow.book.borrowed = False
    borrow.save()
    borrow.book.save()
    message = f'{request.user} declined {borrow.borrower.user.username}\'s borrow request for "{borrow.book.title}".'
    return redirect('borrow_book')

@login_required
@department_required(['LI', 'IT'])
def borrow_requests(request):
    borrows_pending = Borrow.objects.filter(status='PENDING')
    borrows_confirmed = Borrow.objects.filter(status='CONFIRMED')
    borrows_cancelled = Borrow.objects.filter(status='CANCELLED')
    return render(request, 'books_db/borrow_requests.html', {
        'borrows_pending': borrows_pending,
        'borrows_confirmed': borrows_confirmed,
        'borrows_cancelled': borrows_cancelled,
    })


@login_required
def query_reader_return(request):
    if request.method == 'POST':
        form = ReaderIDForm(request.POST, user=request.user)
        if form.is_valid():
            reader_id = form.cleaned_data['reader_id']
            return redirect('return_book', reader_id=reader_id)
    else:
        form = ReaderIDForm(user=request.user.reader_profile)
    
    return render(request, 'books_db/query_reader.html', {'form': form})


@login_required
def query_reader_fine(request):
    if request.method == 'POST':
        form = ReaderIDForm(request.POST)
        if form.is_valid():
            reader_id = form.cleaned_data['reader_id']
            return redirect('collect_fine', reader_id=reader_id)
    else:
        form = ReaderIDForm()
    return render(request, 'books_db/query_reader.html', {'form': form})


@login_required
def return_book(request, reader_id):
    reader = get_object_or_404(Reader, pk=reader_id)
    return_instance = None

    if request.method == 'POST':
        form = BorrowReturnForm(request.POST, reader=reader)
        if form.is_valid():
            return_instance = form.save(commit=False)
            return_instance.reader = reader
            return_instance.save()
            logger.debug(f"Return instance created: {return_instance}")
            message = f'{return_instance.borrow.borrower.user.username} returned {return_instance.borrow.book.title}.'
            return redirect(f"{reverse('return_book', kwargs={'reader_id': reader_id})}?return_id={return_instance.id}")
        else:
            logger.debug(f"Form is not valid: {form.errors}")
            print(f"Form is not valid: {form.errors}")
    else:
        form = BorrowReturnForm(reader=reader)

    return_id = request.GET.get('return_id')
    if return_id:
        return_instance = get_object_or_404(Return, id=return_id)

    logger.debug(f"Reader: {reader}")
    logger.debug(f"Return instance: {return_instance}")
    return render(request, 'books_db/return_book.html', {'form': form, 'reader': reader, 'return_instance': return_instance})

@login_required
@department_required(['LI', 'IT'])
def return_receipt(request, return_id):
    return_instance = get_object_or_404(Return, id=return_id)
    return render(request, 'books_db/return_receipt.html', {'return_instance': return_instance})


@login_required
@department_required(['TR', 'IT'])
def collect_fine(request, reader_id):
    reader = get_object_or_404(Reader, pk=reader_id)
    fine_collection = None

    if request.method == 'POST':
        form = FineCollectionForm(request.POST)
        if form.is_valid():
            fine_collection = form.save(commit=False)
            fine_collection.reader = reader
            fine_collection.collector = request.user
            fine_collection.fine_amount = reader.owed_money
            fine_collection.save()
            # Set a flag in the session to indicate the fine was just collected
            request.session['fine_collected'] = fine_collection.id
            return redirect('collect_fine', reader_id=reader_id)  # Redirect to avoid resubmission
    else:
        form = FineCollectionForm()

    # Check if the fine was just collected to display the receipt
    fine_collected_id = request.session.get('fine_collected')
    if fine_collected_id:
        fine_collection = get_object_or_404(Fine, id=fine_collected_id)
        # Clear the session flag after displaying the receipt
        del request.session['fine_collected']

    return render(request, 'books_db/collect_fine.html', {
        'form': form,
        'reader': reader,
        'fine': fine_collection,
    })

@login_required
def update_borrows(request):
    if request.method == 'POST':
        for borrow in Borrow.objects.filter(return_date__isnull=True):
            due_date_field = f'due_date_{borrow.id}'
            return_field = f'return_{borrow.id}'
            if due_date_field in request.POST:
                borrow.due_date = request.POST[due_date_field]
            if return_field in request.POST:
                borrow.return_date = request.POST[return_field]
                borrow.book.borrowed = False
                borrow.book.save()
            borrow.save()
    return redirect('/borrow')  # Redirect to the borrow_books view


@login_required
def lost_report(request):
    if request.method == 'POST':
        form = LostRepForm(request.POST)
        if form.is_valid():
            lost_report = form.save(commit=False)
            lost_report.receiver = request.user  # Set the receiver to the current logged-in user
            lost_report.save()
            return redirect('/lost_report')
    else:
        form = LostRepForm()

    lost_reports = LostReport.objects.all()
    return render(request, 'books_db/lost_report.html', {'form': form, 'lost_reports': lost_reports})


@login_required
def removal_report(request):
    error = None
    if request.method == 'POST':
        form = RemovalRepForm(request.POST)
        if form.is_valid():
            removal_report = form.save(commit=False)
            removal_report.remover = request.user  # Set the remover to the current logged-in user
            
            try:
                # Save the removal report first
                removal_report.save()
                logger.info(f"Removal report saved: {removal_report}")

                # Delete the book after saving the removal report
                book = removal_report.book
                book.delete()
                logger.info(f"Book {book.id} deleted by {request.user.username}")

                return redirect('/removal_report')
            except Exception as e:
                logger.error(f"Error while saving removal report or deleting book: {e}")
                error = str(e)
        else:
            logger.debug(f"Form is not valid: {form.errors}")
    else:
        form = RemovalRepForm()

    removal_reports = RemovalReport.objects.all()
    return render(request, 'books_db/removal_report.html', {'form': form, 'removal_reports': removal_reports, 'error': error})





class BookListView(View):
    def get(self, request):
        return render(request, 'books_db/book_list.html')

class BookQueryView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        books = Book.objects.filter(
            Q(title__icontains=query) | 
            Q(author__icontains=query) | 
            Q(categories__icontains=query)
        )
        user_borrow_requests = Borrow.objects.filter(borrower=request.user.reader_profile, status__in=['PENDING', 'CONFIRMED'])
        requested_books = user_borrow_requests.values_list('book_id', flat=True)
        
        book_list = list(books.values('id', 'title', 'author', 'categories', 'publication_year', 'thumbnail'))
        for book in book_list:
            book['requested'] = book['id'] in requested_books
        return JsonResponse(book_list, safe=False)

class ReaderListView(View):
    def get(self, request):
        return render(request, 'books_db/reader_list.html')
    
class ReaderQueryView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        readers = Reader.objects.filter(
            Q(user__username__icontains=query) |
            Q(id__icontains=query) | 
            Q(reader_type__icontains=query)
        )
        reader_list = list(readers.values('id', 'user__username', 'reader_type', 'owed_money', 'credit_score'))
        return JsonResponse(reader_list, safe=False)

def borrow_report(request):
    month = request.GET.get('month', timezone.now().strftime('%Y-%m'))
    year, month = map(int, month.split('-'))
    
    borrows = Borrow.objects.filter(borrow_date__year=year, borrow_date__month=month)
    total_borrows = borrows.count()
    
    borrow_stats = borrows.values('book__genre').annotate(
        borrow_count=Count('id')
    ).order_by('-borrow_count')

    for stat in borrow_stats:
        stat['percentage'] = (stat['borrow_count'] / total_borrows) * 100

    context = {
        'month': f'{year}-{month:02}',
        'borrow_stats': borrow_stats,
        'total_borrows': total_borrows
    }
    
    return render(request, 'books_db/borrow_report.html', context)

@login_required
def overdue_books_report(request):
    today = timezone.now().date()
    borrows = Borrow.objects.filter(due_date__lt=today, return_date__isnull=True)
    
    overdue_books = []
    for borrow in borrows:
        days_overdue = (today - borrow.due_date).days
        overdue_books.append({
            'book_title': borrow.book.title,
            'borrow_date': borrow.borrow_date,
            'days_overdue': days_overdue
        })

    context = {
        'date': today,
        'overdue_books': overdue_books
    }

    return render(request, 'books_db/overdue_books_report.html', context)


@login_required
def fines_report(request):
    today = timezone.now().date()
    readers_with_fines = Reader.objects.filter(owed_money__gt=0)
    
    total_fines = readers_with_fines.aggregate(total=Sum('owed_money'))['total'] or 0

    context = {
        'date': today,
        'readers_with_fines': readers_with_fines,
        'total_fines': total_fines
    }

    return render(request, 'books_db/fines_report.html', context)

@login_required
def calendar_view(request):
    today = timezone.now().date()
    day_borrows = Borrow.objects.filter(borrow_date=today)
    week_borrows = Borrow.objects.filter(borrow_date__gte=today, borrow_date__lt=today + timedelta(days=7))
    month_borrows = Borrow.objects.filter(borrow_date__gte=today, borrow_date__lt=today + timedelta(days=30))

    context = {
        'day_borrows': day_borrows,
        'week_borrows': week_borrows,
        'month_borrows': month_borrows,
    }
    return render(request, 'books_db/calendar_view.html', context)


@login_required
@department_required(['LI', 'IT'])
def query_reader(request):
    if request.method == 'POST':
        form = ReaderIDForm(request.POST, user=request.user)
        if form.is_valid():
            reader_id = form.cleaned_data['reader_id']
            return redirect('reader_management_view', reader_id=reader_id)
    else:
        form = ReaderIDForm(user=request.user)
    
    return render(request, 'books_db/query_reader.html', {'form': form})


@login_required
@department_required(['LI', 'IT'])
def reader_management_view(request, reader_id):
    reader = get_object_or_404(Reader, pk=reader_id)
    active_borrows = Borrow.objects.filter(return_date__isnull=True, borrower=reader, status='CONFIRMED')
    past_borrows = Borrow.objects.filter(return_date__isnull=False, borrower=reader)
    fine_collection = None

    if request.method == 'POST':
        if 'return_book' in request.POST:
            borrow_id = request.POST.get('borrow_id')
            borrow = get_object_or_404(Borrow, id=borrow_id)
            borrow.return_date = timezone.now().date()
            borrow.status = 'RETURNED'  # Update the status if needed
            borrow.save()
            return redirect('reader_management', reader_id=reader_id)
        elif 'collect_fine' in request.POST:
            fine_form = FineCollectionForm(request.POST)
            if fine_form.is_valid():
                fine_collection = fine_form.save(commit=False)
                fine_collection.reader = reader
                fine_collection.collector = request.user
                fine_collection.fine_amount = reader.owed_money
                fine_collection.save()
                return redirect('reader_management', reader_id=reader_id)
    else:
        fine_form = FineCollectionForm()

    context = {
        'reader': reader,
        'active_borrows': active_borrows,
        'past_borrows': past_borrows,
        'fine_form': fine_form,
        'fine_collection': fine_collection,
    }

    return render(request, 'books_db/reader_management.html', context)



def test_view(request):
    reader = request.user
    return render(request, 'books_db/test.html', {'reader': reader})



@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = ReaderBorrowForm(request.POST, user=request.user)
        if form.is_valid():
            borrow = form.save(commit=False)
            try:
                borrow.borrower = request.user.reader_profile
                borrow.status = 'PENDING'  # Initial status when request is made
                borrow.save()
                subject = f'New Book Borrowing Request from {request.user.username}'
                message_body = f'You sent a request to borrow "{borrow.book.title}".'

                # Details for iCal event
                ical_event_details = {
                    'summary': f'Borrowed: {borrow.book.title}',
                    'dtstart': borrow.request_date,
                    'dtend': borrow.request_date,  # Assuming 4 days borrow period
                    'description': f'Book: {borrow.book.title}\nBorrower: {borrow.borrower.user.username}',
                    'location': 'Library Address',  # Customize as needed
                    'uid': f'{borrow.id}@librarysystem.com'
                }

                create_notification(subject, request.user, message_body, ical_event_details=ical_event_details)

                # Send email notification to the LI department
                send_notification_email_to_department(
                    subject='New Book Borrow Request',
                    message=message_body,
                    department='IT'
                )

                return JsonResponse({'success': True})
            except ObjectDoesNotExist:
                form.add_error(None, 'Reader profile not found for the current user.')
                return JsonResponse({'success': False, 'error': 'Reader profile not found.'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ReaderBorrowForm(user=request.user)

    user_borrow_requests = Borrow.objects.filter(borrower=request.user.reader_profile, status__in=['PENDING', 'CONFIRMED'])
    requested_books = user_borrow_requests.values_list('book_id', flat=True)

    return render(request, 'books_db/book_detail.html', {
        'book': book,
        'form': form,
        'requested_books': requested_books
    })



def search_books(request):
    query = request.GET.get('q')
    books = Book.objects.filter(title__icontains=query) if query else Book.objects.all()
    return render(request, 'books_db/search_results.html', {'books': books, 'query': query})


@login_required
def account_view(request):
    user = get_object_or_404(CustomUser, pk=request.user.pk)
    return render(request, 'users/account.html', {'user': user})