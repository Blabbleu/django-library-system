from django.contrib import admin
from .models import Book, Borrow
# Register your models here.
from django.contrib import admin
from .models import *

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title','isbn', 'genre', 'author', 'publication_year', 'borrowed')
    search_fields = ('id', 'title','isbn', 'author', 'genre')
    list_filter = ('genre', 'borrowed')

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrow_date', 'due_date', 'return_date')
    search_fields = ('book__title', 'borrower__full_name')
    list_filter = ('borrow_date', 'due_date', 'return_date')

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('borrow', 'return_date', 'fine_amount', 'previous_dues', 'total_dues')
    search_fields = ('borrow__book__title', 'borrow__borrower__full_name')
    list_filter = ('return_date',)

@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ('reader', 'fine_amount', 'return_amount', 'collector', 'collection_date', 'present_dues')
    search_fields = ('reader__full_name', 'collector__username')
    list_filter = ('collection_date',)

@admin.register(LostReport)
class MissReportAdmin(admin.ModelAdmin):
    list_display = ('book', 'reporter', 'report_date')
    search_fields = ('book__title', 'reporter__username')
    list_filter = ('report_date',)

@admin.register(RemovalReport)
class RemovalReportAdmin(admin.ModelAdmin):
    list_display = ('book', 'remover', 'removal_date', 'reason')
    list_filter = ('remover__department', 'removal_date', 'reason')
