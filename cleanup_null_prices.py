#!/usr/bin/env python
"""
Script para limpiar registros de MaterialSupplier con price NULL
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from catalog.models import MaterialSupplier


def cleanup_null_prices():
    """Elimina registros de MaterialSupplier con price NULL"""
    try:
        # Buscar registros con price NULL
        null_price_records = MaterialSupplier.objects.filter(price__isnull=True)
        count = null_price_records.count()

        if count == 0:
            print("✅ No se encontraron registros con price NULL. Todo está bien.")
            return

        print(f"🔍 Se encontraron {count} registros con price NULL:")
        for record in null_price_records:
            print(
                f"  - ID: {record.id}, Material: {record.material.sku}, Proveedor: {record.supplier.name}"
            )

        # Eliminar los registros problemáticos
        deleted_count, _ = null_price_records.delete()
        print(f"🗑️  Se eliminaron {deleted_count} registros problemáticos.")
        print("✅ Limpieza completada.")

    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")


if __name__ == "__main__":
    cleanup_null_prices()
