from django.urls import path, re_path
from . import views
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    # Home
    path('', views.index, name='index'),

    # Authentication
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Book Management
    path('new_book/', views.new_book, name='new_book'),
    path('books/', BookListView.as_view(), name='book_list'),
    path('books/query/', BookQueryView.as_view(), name='query_books'),
    path('readers/query_books/', BookQueryView.as_view(), name='query_books_reader'),
    re_path(r'^books/(?P<book_id>[A-Za-z0-9-]+)/details/$', views.book_detail, name='book_detail'),
    path('lost_report/', views.lost_report, name='lost_report'),
    path('removal_report/', views.removal_report, name='removal_report'),

    # Borrowing Management
    path('borrow/', views.borrow_books, name='borrow_book'),
    path('borrow_requests/', views.borrow_requests, name='borrow_requests'),
    path('confirm_borrow_request/<int:borrow_id>/', views.confirm_borrow_request, name='confirm_borrow_request'),
    path('cancel_borrow_request/<int:borrow_id>/', views.cancel_borrow_request, name='cancel_borrow_request'),
    path('update_borrows/', views.update_borrows, name='update_borrows'),
    path('borrow_report/', views.borrow_report, name='borrow_report'),
    path('overdue_books_report/', views.overdue_books_report, name='overdue_books_report'),

    # Return Management
    path('return_book/<int:reader_id>/', views.return_book, name='return_book'),
    path('return_book/', views.query_reader_return, name='query_reader_return'),
    path('return_receipt/<int:return_id>/', views.return_receipt, name='return_receipt'),

    # Fine Management
    path('fine/', views.query_reader_fine, name='query_reader_fine'),
    path('fine/<int:reader_id>/', views.collect_fine, name='collect_fine'),
    path('fines_report/', views.fines_report, name='fines_report'),

    # Reader Management
    path('readers/', ReaderListView.as_view(), name='reader_list'),
    path('readers/query/', ReaderQueryView.as_view(), name='reader_query'),
    path('readers/manage/<int:reader_id>/', reader_management_view, name='reader_management'),
    path('readers/borrow', views.borrow_books_reader, name='borrow_books_reader'),

    # Calendar
    path('calendar/', views.calendar_view, name='calendar_view'),

    # Search
    path('search/', views.search_books, name='search_books'),

    # Test
    path('test/', views.test_view, name='test_view'),

    # Account
    path('account/', views.account_view, name='account_view'),
]
