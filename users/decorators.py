from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(*roles):
    def deco(view):
        @wraps(view)
        @login_required
        def _wrapped(request, *a, **kw):
            if request.user.is_superuser or request.user.role in roles:
                return view(request, *a, **kw)
            raise PermissionDenied  # 403
        return _wrapped
    return deco
