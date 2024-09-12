"""
Forms module for the users app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from apps.books_db.models import Borrow
from .models import CustomUser, Reader

class StaffLoginForm(forms.Form):
    """Form for staff login."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

class StaffRegForm(forms.ModelForm):
    """Form for staff registration."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm Password"
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'date_of_birth',
            'address', 'phone_number', 'level_of_education', 'department', 'position'
        ]
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
    """Form for reader registration."""
    reader_type = forms.ChoiceField(choices=Reader.READER_TYPE_CHOICES)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password1',
            'password2', 'reader_type', 'date_of_birth', 'address'
        ]

class ReaderAdminForm(forms.ModelForm):
    """Form for admin to manage readers."""
    class Meta:
        model = Reader
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:  # Check if this form is bound to an existing instance
            self.fields['borrowed_books'].queryset = Borrow.objects.filter(borrower=self.instance, status='CONFIRMED')

User = get_user_model()

class UpdateUserForm(UserChangeForm):
    """Form for updating user information."""
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'date_of_birth', 'address', 'phone_number'
        ]

class ProfilePictureForm(forms.ModelForm):
    """Form for updating profile picture."""
    class Meta:
        model = User
        fields = ['profile_picture']

class CustomPasswordChangeForm(PasswordChangeForm):
    """Form for changing password."""
    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
