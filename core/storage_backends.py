"""
Custom storage para asegurar que las imágenes se suban a S3
"""
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage personalizado para archivos media (imágenes)
    Asegura que todas las imágenes se suban a S3
    """
    location = ''  # Raíz del bucket
    file_overwrite = False  # No sobrescribir archivos
    default_acl = None  # Usar permisos del bucket
