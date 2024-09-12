"""
Views module for the users app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .forms import (
    StaffLoginForm, StaffRegForm, ReaderRegistrationForm, UpdateUserForm,
    ProfilePictureForm, CustomPasswordChangeForm
)
from .models import Reader


def staff_login(request):
    """
    Handle staff login.
    """
    if request.method == 'POST':
        form = StaffLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and hasattr(user, 'department'):
                login(request, user)
                return redirect(reverse('index'))  # Redirect to the index page
            messages.error(request, 'Invalid username or password.')
    else:
        form = StaffLoginForm()
    return render(request, 'users/staff_login.html', {'form': form})

@login_required
def reg_staff(request):
    """
    Handle staff registration.
    """
    if request.method == 'POST':
        form = StaffRegForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/register/staff/')
    else:
        form = StaffRegForm()
    return render(request, 'users/reg_staff.html', {'form': form})

def reg_reader(request):
    """
    Handle reader registration.
    """
    if request.method == 'POST':
        form = ReaderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Reader.objects.create(
                user=user,
                date_of_birth=form.cleaned_data['date_of_birth'],
                address=form.cleaned_data['address'],
                reader_type=form.cleaned_data['reader_type']
            )
            return redirect('index')  # Redirect to some view
    else:
        form = ReaderRegistrationForm()
    return render(request, 'users/reg_reader.html', {'form': form})

@login_required
def account_view(request):
    """
    View and update account details.
    """
    user_form = UpdateUserForm(instance=request.user)
    picture_form = ProfilePictureForm(instance=request.user)
    password_form = CustomPasswordChangeForm(user=request.user)
    user = request.user
    if request.method == 'POST':
        if 'update_account' in request.POST:
            user_form = UpdateUserForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                return redirect('account_view')
        elif 'change_picture' in request.POST:
            picture_form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
            if picture_form.is_valid():
                picture_form.save()
                return JsonResponse({'profile_picture_url': request.user.profile_picture.url})
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                return redirect('account_view')

    return render(request, 'users/account.html', {
        'user_form': user_form,
        'picture_form': picture_form,
        'password_form': password_form,
        'user': user,
    })

@login_required
@csrf_exempt
def update_profile_picture(request):
    """
    Update profile picture via AJAX.
    """
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return JsonResponse({'profile_picture_url': request.user.profile_picture.url})
        return JsonResponse({'error': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
@csrf_exempt
def update_account(request):
    """
    Update account details via AJAX.
    """
    if request.method == 'POST':
        user = request.user
        form = UpdateUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'profile_picture_url': user.profile_picture.url})
        return JsonResponse({'error': 'Invalid form submission'}, status=400)
    return render(request, 'users/update_account.html', {'form': UpdateUserForm(instance=request.user)})

@login_required
def change_password(request):
    """
    Handle password change.
    """
    if request.method == 'POST':
        password_form = CustomPasswordChangeForm(request.user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('account_view')
        messages.error(request, 'Please correct the error below.')
    else:
        password_form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'password_form': password_form
    })
