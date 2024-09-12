"""
Form definitions for the books_db app.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Book, Borrow, Return, Fine, LostReport, RemovalReport, BookList


class BorrowForm(forms.ModelForm):
    """Form for borrowing books."""
    class Meta:
        model = Borrow
        fields = ['book', 'borrower']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.exclude(borrow__status='CONFIRMED')


class ReaderBorrowForm(forms.ModelForm):
    """Form for readers to borrow books."""
    class Meta:
        model = Borrow
        fields = ['book', 'borrower', 'request_date']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.exclude(borrow__status='CONFIRMED')
        self.fields['request_date'].widget = forms.DateInput(attrs={'type': 'datetime-local'})
        if user and hasattr(user, 'reader_profile'):
            self.fields['borrower'].initial = user.reader_profile
            self.fields['borrower'].widget = forms.HiddenInput()


class ReaderIDForm(forms.Form):
    """Form for Reader ID."""
    reader_id = forms.IntegerField(label='Reader ID', required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'reader_profile'):
            self.fields['reader_id'].initial = user.reader_profile.id
            self.fields['reader_id'].widget = forms.HiddenInput()


class BorrowReturnForm(forms.ModelForm):
    """Form for returning borrowed books."""
    class Meta:
        model = Return
        fields = ['borrow']

    def __init__(self, *args, **kwargs):
        self.reader = kwargs.pop('reader', None)
        super().__init__(*args, **kwargs)
        if self.reader:
            self.fields['borrow'].queryset = Borrow.objects.filter(borrower=self.reader, return_date__isnull=True, status='CONFIRMED')


class FineCollectionForm(forms.ModelForm):
    """Form for collecting fines."""
    class Meta:
        model = Fine
        fields = ['return_amount']

    def __init__(self, *args, **kwargs):
        self.reader = kwargs.pop('reader', None)
        super().__init__(*args, **kwargs)
        if self.reader:
            self.fields['return_amount'].label = f'Return amount (Current dues: ${self.reader.owed_money})'


class BookRegForm(forms.ModelForm):
    """Form for registering books."""
    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'genre', 'language', 'author', 'publication_year',
            'publisher', 'description', 'page_count', 'categories',
            'thumbnail', 'value'
        ]


class LostRepForm(forms.ModelForm):
    """Form for reporting lost books."""
    class Meta:
        model = LostReport
        fields = ['book', 'reporter']


class RemovalRepForm(forms.ModelForm):
    """Form for reporting book removals."""
    book = forms.ModelChoiceField(queryset=Book.objects.all())

    class Meta:
        model = RemovalReport
        fields = ['book', 'reason']


class ISBNForm(forms.Form):
    """Form for ISBN input."""
    isbn = forms.CharField(label='ISBN', max_length=13)


class BookListForm(forms.ModelForm):
    """Form for creating book lists."""
    class Meta:
        model = BookList
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if BookList.objects.filter(name=name, user=self.user).exists():
            raise ValidationError('You already have a list with this name.')
        return name
