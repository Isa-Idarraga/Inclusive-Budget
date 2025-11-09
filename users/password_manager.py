"""
Gestor de contraseñas visibles para usuarios no-JEFE
Almacena las contraseñas en un archivo JSON para que el JEFE pueda verlas
"""
import json
import os
from django.conf import settings


class PasswordManager:
    """Gestiona el almacenamiento de contraseñas visibles"""
    
    # Archivo donde se guardarán las contraseñas
    PASSWORD_FILE = os.path.join(settings.BASE_DIR, 'users', 'user_passwords.json')
    
    @classmethod
    def _load_passwords(cls):
        """Carga las contraseñas desde el archivo JSON"""
        if os.path.exists(cls.PASSWORD_FILE):
            try:
                with open(cls.PASSWORD_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    @classmethod
    def _save_passwords(cls, passwords):
        """Guarda las contraseñas en el archivo JSON"""
        with open(cls.PASSWORD_FILE, 'w', encoding='utf-8') as f:
            json.dump(passwords, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def save_password(cls, username, password, role):
        """
        Guarda la contraseña visible de un usuario
        Solo para roles COMERCIAL y CONSTRUCTOR
        """
        if role in ['COMERCIAL', 'CONSTRUCTOR']:
            passwords = cls._load_passwords()
            passwords[username] = {
                'password': password,
                'role': role
            }
            cls._save_passwords(passwords)
    
    @classmethod
    def get_password(cls, username):
        """Obtiene la contraseña visible de un usuario"""
        passwords = cls._load_passwords()
        return passwords.get(username, {}).get('password', None)
    
    @classmethod
    def delete_password(cls, username):
        """Elimina la contraseña visible de un usuario"""
        passwords = cls._load_passwords()
        if username in passwords:
            del passwords[username]
            cls._save_passwords(passwords)
    
    @classmethod
    def get_all_passwords(cls):
        """Obtiene todas las contraseñas almacenadas"""
        return cls._load_passwords()
