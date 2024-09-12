# urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.staff_login, name='staff_login'),
    path('register/staff/', views.reg_staff, name='reg_staff'),
    path('register/reader/', views.reg_reader, name='reg_reader'),
    path('account/', views.account_view, name='account_view'),
    path('account/update/', views.update_account, name='update_account'),
    path('account/change-password/', views.change_password, name='change_password'),
    path('account/update_picture/', views.update_profile_picture, name='update_profile_picture'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
