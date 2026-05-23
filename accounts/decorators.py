from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles):
    """Декоратор для проверки роли пользователя"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.role not in allowed_roles:
                raise PermissionDenied("У вас нет доступа к этой странице")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def moderator_required(view_func):
    """Декоратор для модераторов"""
    return role_required(['moderator', 'admin'])(view_func)