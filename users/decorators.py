from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps


def role_required(*roles):
    """Decorador que verifica si el usuario tiene uno de los roles especificados"""
    def deco(view):
        @wraps(view)
        @login_required
        def _wrapped(request, *a, **kw):
            if request.user.is_superuser or request.user.role in roles:
                return view(request, *a, **kw)
            raise PermissionDenied  # 403

        return _wrapped

    return deco


def project_owner_or_jefe_required(view):
    """Decorador que verifica si el usuario es dueño del proyecto o es JEFE"""
    @wraps(view)
    @login_required
    def _wrapped(request, *a, **kw):
        from projects.models import Project

        # Buscar project_id en kwargs o en la URL
        project_id = kw.get('project_id') or kw.get('pk')

        if not project_id:
            raise PermissionDenied

        project = Project.objects.filter(id=project_id).first()

        if not project:
            raise PermissionDenied

        # JEFE o superuser tienen acceso total
        if request.user.is_superuser or request.user.role == 'JEFE':
            return view(request, *a, **kw)

        # CONSTRUCTOR solo si es su proyecto
        if request.user.role == 'CONSTRUCTOR' and project.creado_por_id == request.user.id:
            return view(request, *a, **kw)

        raise PermissionDenied

    return _wrapped
