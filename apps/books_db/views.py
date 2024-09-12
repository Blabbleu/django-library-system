import json
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Count, Sum
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView, ListView, FormView, UpdateView, DeleteView
from apps.notifications.utils import create_notification, send_notification_email_to_department
from apps.users.models import Reader
from .models import Book, Borrow, Return, Fine, LostReport, RemovalReport, BookList
from .forms import (
    ISBNForm, BookRegForm, BorrowForm, ReaderBorrowForm,
    ReaderIDForm, BorrowReturnForm, FineCollectionForm,
    LostRepForm, RemovalRepForm, BookListForm
)
from .decorators import department_required
from .utils import get_book_details_from_google_books
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.context import RequestContext

logger = logging.getLogger(__name__)


class IndexView(View):
    """Index view to show the main page."""
    @method_decorator(login_required)
    def get(self, request):
        user_department = request.user.department if request.user.is_authenticated else None
        book_list = Book.objects.all()

        recently_read_books = []
        favorite_books = []
        if request.user.is_authenticated and hasattr(request.user, 'reader_profile'):
            user_borrowed_books = Borrow.objects.filter(
                borrower=request.user.reader_profile,
                status='RETURNED'
            ).order_by('-return_date').distinct()
            seen_book_ids = set()
            for borrow in user_borrowed_books:
                if borrow.book.id not in seen_book_ids:
                    recently_read_books.append(borrow)
                    seen_book_ids.add(borrow.book.id)

            # Retrieve or create favorite books list
            favorite_books_list, created = BookList.objects.get_or_create(
                user=request.user.reader_profile, slug='favorites', defaults={'name': 'Favorites'})
            favorite_books = favorite_books_list.books.all()

        context = {
            'user_department': user_department,
            'book_list': book_list,
            'recently_read_books': recently_read_books,
            'favorite_books': favorite_books,
        }
        return render(request, 'books_db/index.html', context)


class BaseView(View):
    """Base view to show general content."""
    @method_decorator(login_required)
    def get(self, request):
        books_lists = BookList.objects.filter(user=request.user.reader_profile)
        return render(request, 'base_generic.html', {'books_lists': books_lists})


class NewBookView(View):
    """View to register a new book."""
    @method_decorator(login_required)
    @method_decorator(department_required(['WK', 'IT']))
    def get(self, request):
        isbn_form = ISBNForm()
        form = BookRegForm()
        books = Book.objects.all()
        return render(request, 'books_db/new_book.html', {'isbn_form': isbn_form, 'form': form, 'books': books})

    @method_decorator(login_required)
    @method_decorator(department_required(['WK', 'IT']))
    def post(self, request):
        isbn_form = ISBNForm()
        form = BookRegForm()

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


class BorrowBooksView(View):
    """View to borrow books."""
    @method_decorator(login_required)
    def get(self, request):
        form = BorrowForm()
        borrows = Borrow.objects.filter(return_date__isnull=True)
        return render(request, 'books_db/borrow_books.html', {'form': form, 'borrows': borrows})

    @method_decorator(login_required)
    def post(self, request):
        form = BorrowForm(request.POST)
        if form.is_valid():
            borrow = form.save()
            subject = f'New Book Borrowing Request from {borrow.borrower.user.username}'
            message_body = f'You sent a request to borrow "{borrow.book.title}".'

            ical_event_details = {
                'summary': f'Borrowed: {borrow.book.title}',
                'dtstart': borrow.request_date,
                'dtend': borrow.request_date,
                'description': f'Book: {borrow.book.title}\nBorrower: {borrow.borrower.user.username}',
                'location': 'Library Address',
                'uid': f'{borrow.id}@librarysystem.com'
            }

            create_notification(subject, request.user, message_body, ical_event_details=ical_event_details)
            send_notification_email_to_department(
                subject='New Book Borrow Request',
                message=message_body,
                department='IT'
            )
            return redirect('/borrow')
        borrows = Borrow.objects.filter(return_date__isnull=True)
        return render(request, 'books_db/borrow_books.html', {'form': form, 'borrows': borrows})


class BorrowBooksReaderView(View):
    """View for readers to borrow books."""
    @method_decorator(login_required)
    def get(self, request):
        form = ReaderBorrowForm(user=request.user)
        query = request.GET.get('q', '')
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query),
            borrowed=False
        )
        user_borrow_requests = Borrow.objects.filter(borrower=request.user.reader_profile, status__in=['PENDING', 'CONFIRMED'])
        requested_books = user_borrow_requests.values_list('book_id', flat=True)
        return render(request, 'books_db/borrow_books_reader.html', {
            'form': form,
            'books': books,
            'requested_books': requested_books
        })

    @method_decorator(login_required)
    def post(self, request):
        form = ReaderBorrowForm(request.POST, user=request.user)
        if form.is_valid():
            borrow = form.save(commit=False)
            try:
                borrow.borrower = request.user.reader_profile
                borrow.status = 'PENDING'
                borrow.save()
                subject = f'New Book Borrowing Request from {request.user.username}'
                message_body = f'You sent a request to borrow "{borrow.book.title}".'

                ical_event_details = {
                    'summary': f'Borrowed: {borrow.book.title}',
                    'dtstart': borrow.request_date,
                    'dtend': borrow.request_date,
                    'description': f'Book: {borrow.book.title}\nBorrower: {borrow.borrower.user.username}',
                    'location': 'Library Address',
                    'uid': f'{borrow.id}@librarysystem.com'
                }

                create_notification(subject, request.user, message_body, ical_event_details=ical_event_details)
                send_notification_email_to_department(
                    subject='New Book Borrow Request',
                    message=message_body,
                    department='IT'
                )

                return redirect('/readers/borrow')
            except ObjectDoesNotExist:
                form.add_error(None, 'Reader profile not found for the current user.')
        return render(request, 'books_db/borrow_books_reader.html', {
            'form': form,
            'books': Book.objects.filter(borrowed=False),
            'requested_books': Borrow.objects.filter(borrower=request.user.reader_profile, status__in=['PENDING', 'CONFIRMED']).values_list('book_id', flat=True)
        })


class ConfirmBorrowRequestView(View):
    """View to confirm borrow requests."""
    @method_decorator(login_required)
    @method_decorator(department_required(['LI', 'IT']))
    def get(self, request, borrow_id):
        borrow = get_object_or_404(Borrow, pk=borrow_id)
        borrow.status = 'CONFIRMED'
        borrow.book.borrowed = True
        borrow.save()
        borrow.book.save()

        subject = f'Borrow Request for "{borrow.book.title}" Approved'
        message_body = (f'{request.user} approved {borrow.borrower.user.username}\'s borrow request for "{borrow.book.title}",'
                        f'\nYou have picked up "{borrow.book.title}" please return the book on the right date: {borrow.due_date}.')

        borrow_date = timezone.make_aware(datetime.combine(borrow.borrow_date.date(), datetime.min.time()), timezone.get_current_timezone())
        due_date = timezone.make_aware(datetime.combine(borrow.due_date, datetime.min.time()), timezone.get_current_timezone())

        ical_event_details = {
            'summary': f'Picked up: {borrow.book.title}',
            'dtstart': borrow_date,
            'dtend': due_date,
            'description': (f'Reader: {borrow.borrower.user.username}\n Pick up time: {borrow.borrow_date} '
                            f'\n Borrowing period: 4 days\n Due date: {borrow.due_date}'),
            'location': 'Library Address',
            'uid': f'{borrow.id}@librarysystem.com'
        }
        create_notification(
            subject,
            borrow.borrower.user,
            message_body,
            ical_event_details=ical_event_details,
            type='borrow',
            receipt_info=borrow
        )
        return redirect('borrow_book')


class CancelBorrowRequestView(View):
    """View to cancel borrow requests."""
    @method_decorator(login_required)
    @method_decorator(department_required(['LI', 'IT']))
    def get(self, request, borrow_id):
        borrow = get_object_or_404(Borrow, pk=borrow_id)
        borrow.status = 'CANCELLED'
        borrow.book.borrowed = False
        borrow.save()
        borrow.book.save()
        message = f'{request.user} declined {borrow.borrower.user.username}\'s borrow request for "{borrow.book.title}".'
        return redirect('borrow_book')


class BorrowRequestsView(View):
    """View to manage borrow requests."""
    @method_decorator(login_required)
    @method_decorator(department_required(['LI', 'IT']))
    def get(self, request):
        borrows_pending = Borrow.objects.filter(status='PENDING')
        borrows_confirmed = Borrow.objects.filter(status='CONFIRMED')
        borrows_cancelled = Borrow.objects.filter(status='CANCELLED')
        return render(request, 'books_db/borrow_requests.html', {
            'borrows_pending': borrows_pending,
            'borrows_confirmed': borrows_confirmed,
            'borrows_cancelled': borrows_cancelled,
        })


class QueryReaderReturnView(View):
    """View to query reader returns."""
    @method_decorator(login_required)
    def get(self, request):
        form = ReaderIDForm(user=request.user)
        return render(request, 'books_db/query_reader.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        form = ReaderIDForm(request.POST, user=request.user)
        if form.is_valid():
            reader_id = form.cleaned_data['reader_id']
            return redirect('return_book', reader_id=reader_id)
        return render(request, 'books_db/query_reader.html', {'form': form})


class QueryReaderFineView(View):
    """View to query reader fines."""
    @method_decorator(login_required)
    def get(self, request):
        form = ReaderIDForm()
        return render(request, 'books_db/query_reader.html', {'form': form})

    @method_decorator(login_required)
    def post(self, request):
        form = ReaderIDForm(request.POST)
        if form.is_valid():
            reader_id = form.cleaned_data['reader_id']
            return redirect('collect_fine', reader_id=reader_id)
        return render(request, 'books_db/query_reader.html', {'form': form})


class ReturnBookView(FormView):
    template_name = 'books_db/return_book.html'
    form_class = BorrowReturnForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        reader_id = self.kwargs.get('reader_id')
        reader = get_object_or_404(Reader, pk=reader_id)
        kwargs.update({'reader': reader})
        return kwargs

    def form_valid(self, form):
        reader_id = self.kwargs.get('reader_id')
        reader = get_object_or_404(Reader, pk=reader_id)
        return_instance = form.save(commit=False)
        return_instance.reader = reader
        return_instance.save()

        message = f'{return_instance.borrow.borrower.user.username} returned {return_instance.borrow.book.title}.'
        create_notification(
            subject='Book Return Receipt',
            user=reader.user,
            message=message,
            type='return',
            ical_event_details=None,
            receipt_info=return_instance
        )

        return redirect(f"{reverse('return_book', kwargs={'reader_id': reader_id})}?return_id={return_instance.id}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reader_id = self.kwargs.get('reader_id')
        reader = get_object_or_404(Reader, pk=reader_id)
        return_id = self.request.GET.get('return_id')
        return_instance = get_object_or_404(Return, id=return_id) if return_id else None

        context.update({
            'reader': reader,
            'return_instance': return_instance,
        })
        return context


class ReturnReceiptView(DetailView):
    """View to show return receipt."""
    model = Return
    template_name = 'books_db/return_receipt.html'
    context_object_name = 'return_instance'


class CollectFineView(FormView):
    """View to collect fines"""
    template_name = 'books_db/collect_fine.html'
    form_class = FineCollectionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        reader_id = self.kwargs.get('reader_id')
        reader = get_object_or_404(Reader, pk=reader_id)
        kwargs.update({'reader': reader})
        return kwargs

    def form_valid(self, form):
        reader_id = self.kwargs.get('reader_id')
        reader = get_object_or_404(Reader, pk=reader_id)
        fine_collection = form.save(commit=False)
        fine_collection.reader = reader
        fine_collection.collector = self.request.user
        fine_collection.fine_amount = reader.owed_money
        fine_collection.save()

        self.request.session['fine_collected'] = fine_collection.id
        return redirect('collect_fine', reader_id=reader_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reader_id = self.kwargs.get('reader_id')
        reader = get_object_or_404(Reader, pk=reader_id)
        fine_collected_id = self.request.session.pop('fine_collected', None)
        fine_collection = get_object_or_404(Fine, id=fine_collected_id) if fine_collected_id else None

        context.update({
            'reader': reader,
            'fine_collection': fine_collection,
        })
        return context


class UpdateBorrowsView(View):
    def post(self, request, *args, **kwargs):
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
        return redirect('/borrow')


class LostReportView(FormView):
    template_name = 'books_db/lost_report.html'
    form_class = LostRepForm

    def form_valid(self, form):
        lost_report = form.save(commit=False)
        lost_report.receiver = self.request.user
        lost_report.save()
        return redirect('/lost_report')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lost_reports = LostReport.objects.all()
        context.update({'lost_reports': lost_reports})
        return context


class RemovalReportView(FormView):
    template_name = 'books_db/removal_report.html'
    form_class = RemovalRepForm

    def form_valid(self, form):
        removal_report = form.save(commit=False)
        removal_report.remover = self.request.user
        try:
            removal_report.save()
            book = removal_report.book
            book.delete()
            return redirect('/removal_report')
        except Exception as e:
            logger.error("Error while saving removal report or deleting book: %s", e)
            context = self.get_context_data(form=form)
            context['error'] = str(e)
            return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        removal_reports = RemovalReport.objects.all()
        context.update({'removal_reports': removal_reports})
        return context


class BookListView(TemplateView):
    template_name = 'books_db/book_list.html'


class BookQueryView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        category = request.GET.get('category', '')
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(categories__icontains=query)
        )
        if category:
            books = books.filter(categories__icontains=category)

        requested_books = []
        if request.user.is_authenticated and hasattr(request.user, 'reader_profile'):
            user_borrow_requests = Borrow.objects.filter(
                borrower=request.user.reader_profile,
                status__in=['PENDING', 'CONFIRMED']
            )
            requested_books = user_borrow_requests.values_list('book_id', flat=True)

        book_list = list(books.values(
            'id', 'title', 'author', 'categories', 'publication_year', 'thumbnail', 'isbn'
        ))
        for book in book_list:
            book['requested'] = book['id'] in requested_books
        return JsonResponse(book_list, safe=False)


class ReaderListView(TemplateView):
    template_name = 'books_db/reader_list.html'


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


class BorrowReportView(View):
    def get(self, request):
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


class OverdueBooksReportView(View):
    def get(self, request):
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


class FinesReportView(View):
    def get(self, request):
        today = timezone.now().date()
        readers_with_fines = Reader.objects.filter(owed_money__gt=0)

        total_fines = readers_with_fines.aggregate(total=Sum('owed_money'))['total'] or 0

        context = {
            'date': today,
            'readers_with_fines': readers_with_fines,
            'total_fines': total_fines
        }

        return render(request, 'books_db/fines_report.html', context)


class CalendarView(View):
    def get(self, request):
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


class QueryReaderView(FormView):
    template_name = 'books_db/query_reader.html'
    form_class = ReaderIDForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        reader_id = form.cleaned_data['reader_id']
        return redirect('reader_management_view', reader_id=reader_id)


class ReaderManagementView(View):
    def get(self, request, reader_id):
        reader = get_object_or_404(Reader, pk=reader_id)
        active_borrows = Borrow.objects.filter(return_date__isnull=True, borrower=reader, status='CONFIRMED')
        past_borrows = Borrow.objects.filter(return_date__isnull=False, borrower=reader)
        fine_form = FineCollectionForm()

        context = {
            'reader': reader,
            'active_borrows': active_borrows,
            'past_borrows': past_borrows,
            'fine_form': fine_form,
            'fine_collection': None,
        }

        return render(request, 'books_db/reader_management.html', context)

    def post(self, request, reader_id):
        reader = get_object_or_404(Reader, pk=reader_id)

        if 'return_book' in request.POST:
            borrow_id = request.POST.get('borrow_id')
            borrow = get_object_or_404(Borrow, id=borrow_id)
            borrow.return_date = timezone.now().date()
            borrow.status = 'RETURNED'
            borrow.save()
            return redirect('reader_management', reader_id=reader_id)

        if 'collect_fine' in request.POST:
            fine_form = FineCollectionForm(request.POST)
            if fine_form.is_valid():
                fine_collection = fine_form.save(commit=False)
                fine_collection.reader = reader
                fine_collection.collector = request.user
                fine_collection.fine_amount = reader.owed_money
                fine_collection.save()
                return redirect('reader_management', reader_id=reader_id)

        return self.get(request, reader_id)


class BookDetailView(DetailView):
    model = Book
    template_name = 'books_db/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book = self.get_object()
        borrower = None

        if book.borrowed:
            try:
                borrow_instance = Borrow.objects.get(book=book, status='CONFIRMED')
                borrower = borrow_instance.borrower
            except Borrow.DoesNotExist:
                borrower = None

        if self.request.user.is_authenticated and hasattr(self.request.user, 'reader_profile'):
            user_borrow_requests = Borrow.objects.filter(
                borrower=self.request.user.reader_profile,
                status__in=['PENDING', 'CONFIRMED']
            )
            requested_books = user_borrow_requests.values_list('book_id', flat=True)

            context.update({
                'form': ReaderBorrowForm(user=self.request.user),
                'requested_books': requested_books,
                'borrower': borrower
            })

        context['borrower'] = borrower
        return context

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'reader_profile'):
            form = ReaderBorrowForm(request.POST, user=request.user)
            if form.is_valid():
                borrow = form.save(commit=False)
                try:
                    borrow.borrower = request.user.reader_profile
                    borrow.status = 'PENDING'
                    borrow.save()
                    subject = f'New Book Borrowing Request from {request.user.username}'
                    message_body = f'You sent a request to borrow "{borrow.book.title}".'

                    ical_event_details = {
                        'summary': f'Borrowed: {borrow.book.title}',
                        'dtstart': borrow.request_date,
                        'dtend': borrow.request_date,
                        'description': f'Book: {borrow.book.title}\nBorrower: {borrow.borrower.user.username}',
                        'location': 'Library Address',
                        'uid': f'{borrow.id}@librarysystem.com'
                    }

                    create_notification(subject, request.user, message_body, ical_event_details=ical_event_details)
                    send_notification_email_to_department(
                        subject='New Book Borrow Request',
                        message=message_body,
                        department='IT'
                    )

                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': True})
                    else:
                        return redirect(reverse('book_detail', args=[self.get_object().id]))
                except ObjectDoesNotExist:
                    form.add_error(None, 'Reader profile not found for the current user.')
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Reader profile not found.'})
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': form.errors})

        return self.get(request, *args, **kwargs)


class SearchBooksView(View):
    def get(self, request):
        query = request.GET.get('q')
        books = Book.objects.filter(title__icontains=query) if query else Book.objects.all()
        return render(request, 'books_db/search_results.html', {'books': books, 'query': query})


class CreateListView(FormView):
    template_name = 'books_db/create_list.html'
    form_class = BookListForm

    def form_valid(self, form):
        new_list = form.save(commit=False)
        new_list.user = self.request.user.reader_profile
        new_list.save()
        return redirect('lists')


class ListsView(View):
    def get(self, request):
        reader_profile = request.user.reader_profile
        ready_made_lists = BookList.objects.filter(user=reader_profile, ready_made=True)
        custom_lists = BookList.objects.filter(user=reader_profile, ready_made=False)
        book_list = Book.objects.all()

        context = {
            'ready_made_lists': ready_made_lists,
            'custom_lists': custom_lists,
            'form': BookListForm(user=reader_profile),
            'book_list': book_list,
            'book_lists': custom_lists | ready_made_lists,  # Add this line
        }

        return render(request, 'books_db/personal_lists.html', context)

    def post(self, request):
        reader_profile = request.user.reader_profile
        form = BookListForm(request.POST, user=reader_profile)
        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.user = reader_profile
            new_list.save()
            return redirect('personal_lists')


@login_required
@csrf_exempt
def add_favorite(request):
    """View to add a book to favorites."""
    if request.method == 'POST':
        data = json.loads(request.body)
        book_id = data.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
            favorites_list, created = BookList.objects.get_or_create(user=request.user.reader_profile, slug='favorites')
            favorites_list.books.add(book)
            return JsonResponse({'success': True})
        except Book.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Book not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def remove_favorite(request):
    """View to remove a book from favorites."""
    if request.method == 'POST':
        data = json.loads(request.body)
        book_id = data.get('book_id')
        try:
            book = Book.objects.get(id=book_id)
            favorites_list, created = BookList.objects.get_or_create(user=request.user.reader_profile, slug='favorites')
            favorites_list.books.remove(book)
            return JsonResponse({'success': True})
        except (Book.DoesNotExist, BookList.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Book or favorites list not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


class ListDetailsView(DetailView):
    model = BookList
    template_name = 'books_db/lists_details.html'
    context_object_name = 'book_list'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        book_list = self.get_object()
        books = book_list.books.all()
        context.update({
            'books': books,
            'list_name': book_list.name,
            'slug': book_list.slug,
        })
        return context


@login_required
def add_book_to_list(request, slug, book_id):
    """View to add a book to a custom list."""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        book_list = get_object_or_404(BookList, user=request.user.reader_profile, slug=slug)
        book_list.books.add(book)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@csrf_exempt
def remove_book_from_list(request, slug, book_id):
    """View to remove a book from a custom list."""
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        book_list = get_object_or_404(BookList, user=request.user.reader_profile, slug=slug)
        book_list.books.remove(book)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)
