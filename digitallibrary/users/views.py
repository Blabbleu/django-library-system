from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import *
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse

def staff_login(request):
    if request.method == 'POST':
        form = StaffLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None and hasattr(user, 'department'):
                login(request, user)
                return redirect(reverse('index'))  # Redirect to the index page
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = StaffLoginForm()
    return render(request, 'users/staff_login.html', {'form': form})

@login_required
def reg_staff(request):
    if request.method == 'POST':
        form = StaffRegForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/register/staff/')
    else:
        form = StaffRegForm()
    return render(request, 'users/reg_staff.html', {'form': form})

@login_required
def reg_reader(request):
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