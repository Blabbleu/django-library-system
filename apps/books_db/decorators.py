"""
Custom decorators for the books_db app.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied


def department_required(departments):
    """
    Decorator for views that checks whether a user is in a given department,
    raising a PermissionDenied exception if necessary.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.department in departments:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator
