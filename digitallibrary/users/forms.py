# forms.py in users app
from .models import *
from django import forms
from django.contrib.auth.forms import UserCreationForm
from books_db.models import Borrow
from .models import Reader


class StaffLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class StaffRegForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'date_of_birth', 'address', 'phone_number', 'level_of_education', 'department', 'position']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'level_of_education': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class ReaderRegistrationForm(UserCreationForm):
    reader_type = forms.ChoiceField(choices=Reader.READER_TYPE_CHOICES)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'reader_type', 'date_of_birth', 'address']


class ReaderAdminForm(forms.ModelForm):
    class Meta:
        model = Reader
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Check if this form is bound to an existing instance
            self.fields['borrowed_books'].queryset = Borrow.objects.filter(borrower=self.instance, status='CONFIRMED')