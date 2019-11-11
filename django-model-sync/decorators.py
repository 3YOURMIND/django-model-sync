from functools import wraps

from rest_framework import exceptions

from apps.b3_migration.models.switch import Switch


def require_switch(feature_name):
    """
    Decorate any view function or methods of class-based views: get(), post()
    etc or anything, that gets called from these methods, for example
    get_queryset()

    Raises PermissionDenied(), in above-mentioned methods DRF gracefully
    handles this exception and returns 403 Forbidden response with error
    details
    """
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if Switch.is_active(feature_name):
                return func(*args, **kwargs)
            else:
                raise exceptions.PermissionDenied(
                    f'This API is not available without {feature_name} switch'
                )

        return wrapper

    return decorator
