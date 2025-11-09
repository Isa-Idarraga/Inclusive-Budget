"""
Script para poblar contraseñas de usuarios existentes
Ejecutar: python manage.py shell < users/populate_passwords.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from users.password_manager import PasswordManager

# Contraseña por defecto para usuarios existentes
DEFAULT_PASSWORD = "changeme123"

# Obtener todos los usuarios COMERCIAL y CONSTRUCTOR
users = User.objects.filter(role__in=['COMERCIAL', 'CONSTRUCTOR'])

print(f"\n{'='*60}")
print(f"POBLAR CONTRASEÑAS DE USUARIOS EXISTENTES")
print(f"{'='*60}\n")

if not users.exists():
    print("❌ No hay usuarios COMERCIAL o CONSTRUCTOR en el sistema.\n")
else:
    print(f"📋 Encontrados {users.count()} usuarios para procesar:\n")
    
    for user in users:
        # Asignar contraseña por defecto
        user.set_password(DEFAULT_PASSWORD)
        user.save()
        
        # Guardar en el archivo JSON
        PasswordManager.save_password(user.username, DEFAULT_PASSWORD, user.role)
        
        print(f"✅ {user.username} ({user.get_role_display()}) → Contraseña: {DEFAULT_PASSWORD}")
    
    print(f"\n{'='*60}")
    print(f"✅ PROCESO COMPLETADO")
    print(f"{'='*60}")
    print(f"\n💡 Ahora puedes ver las contraseñas en la tabla de usuarios.")
    print(f"💡 Los usuarios pueden iniciar sesión con: {DEFAULT_PASSWORD}\n")
