"""
Minimal settings override for running tests locally with SQLite.
This imports all settings from core.settings then replaces DATABASES to use SQLite
to avoid creating/dropping test DBs on remote Postgres instances.
"""
from .settings import *  # noqa: F401,F403

# Use a local SQLite DB for tests to avoid touching remote Postgres
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_sqlite3.db',
    }
}

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Keep other settings from core.settings
