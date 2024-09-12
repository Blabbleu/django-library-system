"""
URL configuration for books_db app.
"""

from django.urls import path, re_path
from apps.books_db import views
from django.contrib.auth import views as auth_views
from .views import (
    BookListView, BookQueryView, ReaderListView, ReaderQueryView, IndexView,
    NewBookView, BorrowBooksView, BorrowBooksReaderView, ConfirmBorrowRequestView,
    CancelBorrowRequestView, BorrowRequestsView, QueryReaderReturnView, ReturnBookView,
    ReturnReceiptView, QueryReaderFineView, CollectFineView, FinesReportView,
    LostReportView, RemovalReportView, ReaderManagementView, CalendarView,
    SearchBooksView, ListsView, ListDetailsView,
     BorrowReportView, OverdueBooksReportView, BookDetailView, UpdateBorrowsView
)

urlpatterns = [
    # Home
    path('', IndexView.as_view(), name='index'),

    # Authentication
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Book Management
    path('new_book/', NewBookView.as_view(), name='new_book'),
    path('books/', BookListView.as_view(), name='book_list'),
    path('books/query/', BookQueryView.as_view(), name='query_books'),
    path('readers/query_books/', BookQueryView.as_view(), name='query_books_reader'),
    re_path(r'^books/(?P<pk>[A-Za-z0-9-]+)/details/$', BookDetailView.as_view(), name='book_detail'),
    path('lost_report/', LostReportView.as_view(), name='lost_report'),
    path('removal_report/', RemovalReportView.as_view(), name='removal_report'),

    # Borrowing Management
    path('borrow/', BorrowBooksView.as_view(), name='borrow_book'),
    path('borrow_requests/', BorrowRequestsView.as_view(), name='borrow_requests'),
    path('confirm_borrow_request/<str:borrow_id>/', ConfirmBorrowRequestView.as_view(), name='confirm_borrow_request'),
    path('cancel_borrow_request/<str:borrow_id>/', CancelBorrowRequestView.as_view(), name='cancel_borrow_request'),
    path('update_borrows/', UpdateBorrowsView.as_view(), name='update_borrows'),
    path('borrow_report/', BorrowReportView.as_view(), name='borrow_report'),
    path('overdue_books_report/', OverdueBooksReportView.as_view(), name='overdue_books_report'),

    # Return Management
    path('return_book/<int:reader_id>/', ReturnBookView.as_view(), name='return_book'),
    path('return_book/', QueryReaderReturnView.as_view(), name='query_reader_return'),
    path('return_receipt/<int:return_id>/', ReturnReceiptView.as_view(), name='return_receipt'),

    # Fine Management
    path('fine/', QueryReaderFineView.as_view(), name='query_reader_fine'),
    path('fine/<int:reader_id>/', CollectFineView.as_view(), name='collect_fine'),
    path('fines_report/', FinesReportView.as_view(), name='fines_report'),

    # Reader Management
    path('readers/', ReaderListView.as_view(), name='reader_list'),
    path('readers/query/', ReaderQueryView.as_view(), name='reader_query'),
    path('readers/manage/<int:reader_id>/', ReaderManagementView.as_view(), name='reader_management'),
    path('readers/borrow', BorrowBooksReaderView.as_view(), name='borrow_books_reader'),

    # Calendar
    path('calendar/', CalendarView.as_view(), name='calendar_view'),

    # Search
    path('search/', SearchBooksView.as_view(), name='search_books'),

    # Reading lists
    path('lists/', ListsView.as_view(), name='personal_lists'),
    path('lists/<slug:slug>/', ListDetailsView.as_view(), name='lists_details'),
    path('lists/<slug:slug>/add/<str:book_id>/', views.add_book_to_list, name='add_book_to_list'),
    path('lists/<slug:slug>/remove/<str:book_id>/', views.remove_book_from_list, name='remove_book_from_list'),
    path('add_favorite/', views.add_favorite, name='add_favorite'),
    path('remove_favorite/', views.remove_favorite, name='remove_favorite'),
]
