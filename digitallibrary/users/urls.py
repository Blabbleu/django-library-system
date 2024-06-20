from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('register/staff/', views.reg_staff, name='reg_staff'),
    path('register/reader/', views.reg_reader, name='reg_reader'),
]
