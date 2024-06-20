from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import *
from users.models import Reader
from .utils import *

class BorrowForm(forms.ModelForm):
    class Meta:
        model = Borrow
        fields = ['book', 'borrower']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.exclude(borrow__status='CONFIRMED')
        

class ReaderBorrowForm(forms.ModelForm):
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
    reader_id = forms.IntegerField(label='Reader ID', required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and hasattr(user, 'reader_profile'):
            self.fields['reader_id'].initial = user.reader_profile.id
            self.fields['reader_id'].widget = forms.HiddenInput()  # Hide the field if it's auto-filled

class BorrowReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = ['borrow']

    def __init__(self, *args, **kwargs):
        self.reader = kwargs.pop('reader', None)
        super().__init__(*args, **kwargs)
        if self.reader:
            self.fields['borrow'].queryset = Borrow.objects.filter(borrower=self.reader, return_date__isnull=True, status = 'CONFIRMED')

class FineCollectionForm(forms.ModelForm):
    class Meta:
        model = Fine
        fields = ['return_amount']

    def __init__(self, *args, **kwargs):
        self.reader = kwargs.pop('reader', None)
        super().__init__(*args, **kwargs)
        if self.reader:
            self.fields['return_amount'].label = f'Return amount (Current dues: ${self.reader.owed_money})'

class BookRegForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'isbn', 'genre', 'author', 'publication_year',
            'publisher', 'description', 'page_count', 'categories',
            'thumbnail', 'value'
        ]

class LostRepForm(forms.ModelForm):
    class Meta:
        model = LostReport
        fields = ['book', 'reporter']

class RemovalRepForm(forms.ModelForm):
    book = forms.ModelChoiceField(queryset=Book.objects.all())

    class Meta:
        model = RemovalReport
        fields = ['book', 'reason']


class ISBNForm(forms.Form):
    isbn = forms.CharField(label='isbn', max_length=13)
