from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.urls import reverse
from .models import User
from django import forms
from .decorators import role_required


# Formulario personalizado para crear/editar usuarios
class UserManagementForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(),
        required=False,
        help_text="Deja en blanco para mantener la contraseña actual (solo al editar)"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }


def logout_view(request):
    """Vista personalizada de logout que maneja POST y GET"""
    if request.user.is_authenticated:
        auth_logout(request)
        login_url = reverse('users:login')
        return redirect(f"{login_url}?logout=success")
    return redirect('users:login')


@login_required
def home(request):
    mods = []
    for key, label in [
        ("projects", "Proyectos"),
        ("catalog", "Materiales"),
        ("dashboard", "Dashboard"),
    ]:
        if request.user.can_see(key):
            mods.append({"key": key, "label": label})
    return render(request, "home.html", {"modules": mods})


@role_required(User.JEFE)
def user_list(request):
    """Lista todos los usuarios del sistema - Solo JEFE"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users/user_list.html', {'users': users})


@role_required(User.JEFE)
def user_create(request):
    """Crear un nuevo usuario - Solo JEFE"""
    if request.method == 'POST':
        form = UserManagementForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')

            if password:
                user.set_password(password)
            else:
                user.set_password('changeme123')  # Password por defecto

            user.save()
            messages.success(request, f'✅ Usuario "{user.username}" creado exitosamente.')
            return redirect('users:user_list')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario.')
    else:
        form = UserManagementForm()

    return render(request, 'users/user_form.html', {'form': form, 'mode': 'create'})


@role_required(User.JEFE)
def user_update(request, user_id):
    """Editar un usuario existente - Solo JEFE"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get('password')

            if password:
                user.set_password(password)

            user.save()
            messages.success(request, f'✅ Usuario "{user.username}" actualizado exitosamente.')
            return redirect('users:user_list')
        else:
            messages.error(request, '❌ Por favor corrige los errores en el formulario.')
    else:
        form = UserManagementForm(instance=user)

    return render(request, 'users/user_form.html', {
        'form': form,
        'mode': 'update',
        'user_obj': user
    })


@role_required(User.JEFE)
def user_delete(request, user_id):
    """Eliminar un usuario - Solo JEFE"""
    user = get_object_or_404(User, id=user_id)

    # No permitir que se elimine a sí mismo
    if user.id == request.user.id:
        messages.error(request, '❌ No puedes eliminarte a ti mismo.')
        return redirect('users:user_list')

    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'✅ Usuario "{username}" eliminado exitosamente.')
        return redirect('users:user_list')

    return render(request, 'users/user_confirm_delete.html', {'user_obj': user})
