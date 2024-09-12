from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.books_db.models import Book, Borrow, Return, Reader, BookList, LostReport, RemovalReport
from apps.books_db.forms import BookRegForm, BorrowForm, BorrowReturnForm
from datetime import timedelta
from django.core.exceptions import ValidationError
User = get_user_model()

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', department='WK')
        self.reader = Reader.objects.create(
            user=self.user,
            date_of_birth=timezone.now() - timezone.timedelta(days=365*25),
            address='123 Test St',
            reader_type='X'
        )
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            genre='A',
            language='English',
            author='Test Author',
            publication_year=2021,
            publisher='Test Publisher',
            description='Test Description',
            page_count=100,
            categories='Test Category',
            thumbnail='http://example.com/thumbnail.jpg',
            value=10.00,
            receiver=self.user
        )

    def test_book_creation(self):
        self.assertEqual(self.book.title, 'Test Book')
        self.assertEqual(self.book.isbn, '1234567890123')
        self.assertEqual(self.book.genre, 'A')
        self.assertEqual(self.book.language, 'English')
        self.assertEqual(self.book.author, 'Test Author')
        self.assertEqual(self.book.publication_year, 2021)
        self.assertEqual(self.book.publisher, 'Test Publisher')
        self.assertEqual(self.book.description, 'Test Description')
        self.assertEqual(self.book.page_count, 100)
        self.assertEqual(self.book.categories, 'Test Category')
        self.assertEqual(self.book.thumbnail, 'http://example.com/thumbnail.jpg')
        self.assertEqual(self.book.value, 10.00)
        self.assertEqual(self.book.receiver, self.user)

    def test_reader_creation(self):
        self.assertEqual(self.reader.user.username, 'testuser')

class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', department='WK')
        self.reader = Reader.objects.create(
            user=self.user,
            date_of_birth=timezone.now() - timezone.timedelta(days=365*25),
            address='123 Test St',
            reader_type='X'
        )

    def test_valid_book_form(self):
        form_data = {
            'title': 'Test Book',
            'isbn': '1234567890123',
            'genre': 'A',
            'language': 'English',
            'author': 'Test Author',
            'publication_year': 2021,
            'publisher': 'Test Publisher',
            'description': 'Test Description',
            'page_count': 100,
            'categories': 'Test Category',
            'thumbnail': 'http://example.com/thumbnail.jpg',
            'value': 10.00,
            'receiver': self.user.id
        }
        form = BookRegForm(data=form_data)
        self.assertTrue(form.is_valid())

class IntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', department='WK')
        self.reader = Reader.objects.create(
            user=self.user,
            date_of_birth=timezone.now() - timezone.timedelta(days=365*25),
            address='123 Test St',
            reader_type='X'
        )
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            genre='A',
            language='English',
            author='Test Author',
            publication_year=2021,
            publisher='Test Publisher',
            description='Test Description',
            page_count=100,
            categories='Test Category',
            thumbnail='http://example.com/thumbnail.jpg',
            value=10.00,
            receiver=self.user
        )

    def test_borrow_and_return_book(self):
        # Create Borrow instance
        borrow = Borrow.objects.create(
            book=self.book,
            borrower=self.reader,
            status='CONFIRMED'
        )

        # Verify Borrow instance
        self.assertEqual(borrow.status, 'CONFIRMED')

        # Create Return instance
        return_instance = Return.objects.create(
            borrow=borrow,
            reader=self.reader
        )

        # Verify Return instance
        self.assertEqual(return_instance.borrow, borrow)
        self.assertEqual(return_instance.reader, self.reader)
        self.assertEqual(return_instance.borrow.status, 'RETURNED')
        self.assertEqual(return_instance.reader.credit_score, 1)  # Assuming initial credit score was 0 and book was returned on time


class BorrowReturnTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(username='testuser', password='password')
        self.reader = Reader.objects.create(user=self.user,
            date_of_birth=timezone.now() - timezone.timedelta(days=365*25),
            address='123 Test St',
            reader_type='X',
            credit_score=5
        )

        # Create a book
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            genre='A',
            language='English',
            author='Test Author',
            publication_year=2022,
            publisher='Test Publisher',
            receiver=self.user,
            borrowed=False
        )

    def test_borrow_book(self):
        borrow = Borrow.objects.create(
            book=self.book,
            borrower=self.reader,
            status='CONFIRMED'
        )
        self.assertEqual(borrow.status, 'CONFIRMED')
        self.assertEqual(self.book.borrowed, True)
        self.assertEqual(borrow.due_date, borrow.borrow_date + timedelta(days=4))

    def test_return_book_on_time(self):
        borrow = Borrow.objects.create(
            book=self.book,
            borrower=self.reader,
            status='CONFIRMED'
        )
        return_instance = Return.objects.create(
            reader=self.reader,
            borrow=borrow,
            return_date=timezone.now().date()
        )
        self.assertEqual(borrow.status, 'RETURNED')
        self.assertEqual(self.book.borrowed, False)
        self.assertEqual(self.reader.credit_score, 6)  # +1 for on-time return

    def test_return_book_late(self):
        borrow = Borrow.objects.create(
            book=self.book,
            borrower=self.reader,
            status='CONFIRMED'
        )
        return_instance = Return.objects.create(
            reader=self.reader,
            borrow=borrow,
            return_date=timezone.now().date() + timedelta(days=6)  # Late by 2 days
        )
        self.assertEqual(borrow.status, 'RETURNED')
        self.assertEqual(self.book.borrowed, False)
        self.assertEqual(return_instance.fine_amount, 4)  # $2 per day
        self.assertEqual(self.reader.credit_score, 4)  # -2 for late return

    def test_borrow_more_than_allowed_books(self):
        # Borrow 5 books first
        for _ in range(5):
            book = Book.objects.create(
                title=f'Test Book {_}',
                isbn=f'123456789012{_}',
                genre='A',
                language='English',
                author='Test Author',
                publication_year=2022,
                publisher='Test Publisher',
                receiver=self.user,
                borrowed=False
            )
            Borrow.objects.create(
                book=book,
                borrower=self.reader,
                status='CONFIRMED'
            )

        # Try to borrow the 6th book
        with self.assertRaises(ValidationError):
            borrow = Borrow(
                book=self.book,
                borrower=self.reader,
                status='CONFIRMED'
            )
            borrow.full_clean()  # This will call the clean() method

    def test_borrow_with_overdue_books(self):
        # Create an overdue borrow
        borrow = Borrow.objects.create(
            book=self.book,
            borrower=self.reader,
            status='CONFIRMED',
            borrow_date=timezone.now() - timedelta(days=10),
            due_date=timezone.now() - timedelta(days=6)
        )

        # Try to borrow another book
        with self.assertRaises(ValidationError):
            new_book = Book.objects.create(
                title='New Book',
                isbn='9876543210987',
                genre='A',
                language='English',
                author='New Author',
                publication_year=2022,
                publisher='New Publisher',
                receiver=self.user,
                borrowed=False
            )
            new_borrow = Borrow(
                book=new_book,
                borrower=self.reader,
                status='CONFIRMED'
            )
            new_borrow.full_clean()  # This will call the clean() method

    def test_remove_borrow_instance_from_reader_on_return(self):
        borrow = Borrow.objects.create(
            book=self.book,
            borrower=self.reader,
            status='CONFIRMED'
        )
        self.reader.borrowed_books.add(borrow)

        return_instance = Return.objects.create(
            reader=self.reader,
            borrow=borrow,
            return_date=timezone.now().date()
        )
        self.assertNotIn(borrow, self.reader.borrowed_books.all())


class BookListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', department='WK')
        self.reader = Reader.objects.create(
            user=self.user,
            date_of_birth=timezone.now() - timezone.timedelta(days=365*25),
            address='123 Test St',
            reader_type='X'
        )
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            genre='A',
            language='English',
            author='Test Author',
            publication_year=2021,
            publisher='Test Publisher',
            description='Test Description',
            page_count=100,
            categories='Test Category',
            thumbnail='http://example.com/thumbnail.jpg',
            value=10.00,
            receiver=self.user
        )

    def test_create_book_list(self):
        book_list = BookList.objects.create(
            name='Mystery',
            user=self.reader,
            ready_made=True
        )
        book_list.books.add(self.book)
        self.assertEqual(book_list.name, 'Mystery')
        self.assertEqual(book_list.slug, 'mystery')
        self.assertTrue(book_list.ready_made)
        self.assertIn(self.book, book_list.books.all())

    def test_unique_slug(self):
        book_list1 = BookList.objects.create(
            name='Horror',
            user=self.reader,
            ready_made=True
        )
        book_list2 = BookList.objects.create(
            name='Horror 2',
            user=self.reader,
            ready_made=True
        )
        self.assertNotEqual(book_list1.slug, book_list2.slug)


class LostReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', department='WK')
        self.reader = Reader.objects.create(
            user=self.user,
            date_of_birth=timezone.now() - timezone.timedelta(days=365*25),
            address='123 Test St',
            reader_type='X'
        )
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            genre='A',
            language='English',
            author='Test Author',
            publication_year=2021,
            publisher='Test Publisher',
            description='Test Description',
            page_count=100,
            categories='Test Category',
            thumbnail='http://example.com/thumbnail.jpg',
            value=10.00,
            receiver=self.user
        )

    def test_create_lost_report(self):
        lost_report = LostReport.objects.create(
            book=self.book,
            reporter=self.reader,
            receiver=self.user
        )
        self.assertEqual(lost_report.book, self.book)
        self.assertEqual(lost_report.reporter, self.reader)
        self.assertEqual(lost_report.receiver, self.user)
        self.assertEqual(lost_report.fine, self.book.value)
        self.assertEqual(self.reader.owed_money, self.book.value)
        self.assertEqual(self.reader.credit_score, -2)


class RemovalReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345', department='WK')
        self.book = Book.objects.create(
            title='Test Book',
            isbn='1234567890123',
            genre='A',
            language='English',
            author='Test Author',
            publication_year=2021,
            publisher='Test Publisher',
            description='Test Description',
            page_count=100,
            categories='Test Category',
            thumbnail='http://example.com/thumbnail.jpg',
            value=10.00,
            receiver=self.user
        )

    def test_create_removal_report(self):
        removal_report = RemovalReport.objects.create(
            book=self.book,
            remover=self.user,
            reason='L'
        )
        self.assertEqual(removal_report.book, self.book)
        self.assertEqual(removal_report.remover, self.user)
        self.assertEqual(removal_report.reason, 'L')