"""
Pruebas SIMPLIFICADAS para exportación Excel
Cada prueba muestra un mensaje de éxito con checkmark para mejor trazabilidad.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
import sys

User = get_user_model()


def print_success(test_name, description):
    """Imprime mensaje de éxito con checkmark"""
    print(f"✅ {test_name}: {description}", file=sys.stderr)


class ExcelExportBasicTests(TestCase):
    """Pruebas básicas de exportación Excel"""
    
    def setUp(self):
        """Setup mínimo"""
        # Usuarios
        self.jefe = User.objects.create_user(
            username='jefe', password='test123', role=User.JEFE
        )
        self.constructor = User.objects.create_user(
            username='constructor', password='test123', role=User.CONSTRUCTOR
        )
        self.comercial = User.objects.create_user(
            username='comercial', password='test123', role=User.COMERCIAL
        )
        
        self.client = Client()
    
    # ===== PRUEBAS DE AUTENTICACIÓN Y PERMISOS =====
    
    def test_export_budget_requires_login(self):
        """Presupuesto requiere login"""
        response = self.client.get(reverse('projects:export_budget_to_excel', args=[1]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        print_success("AUTENTICACIÓN", "Export presupuesto requiere login correctamente")
    
    def test_export_gastos_requires_login(self):
        """Gastos requiere login"""
        response = self.client.get(reverse('projects:export_gastos_to_excel', args=[1]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        print_success("AUTENTICACIÓN", "Export gastos requiere login correctamente")
    
    def test_export_comparativo_requires_login(self):
        """Comparativo requiere login"""
        response = self.client.get(reverse('projects:export_comparativo_to_excel', args=[1]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        print_success("AUTENTICACIÓN", "Export comparativo requiere login correctamente")
    
    # ===== PRUEBAS DE ROLES =====
    
    def test_export_budget_jefe_role(self):
        """Solo JEFE puede exportar presupuesto"""
        self.client.login(username='jefe', password='test123')
        # Proyecto no existe, pero verifica que no rechaza por rol
        response = self.client.get(reverse('projects:export_budget_to_excel', args=[9999]))
        # 404 es correcto (proyecto no existe), no 403 (sin permisos)
        self.assertEqual(response.status_code, 404)
        print_success("PERMISOS", "Usuario JEFE tiene acceso a export presupuesto")
    
    def test_export_budget_comercial_denied(self):
        """COMERCIAL no puede exportar presupuesto"""
        self.client.login(username='comercial', password='test123')
        response = self.client.get(reverse('projects:export_budget_to_excel', args=[1]))
        # Debe denegar acceso (302 redirige o 403 prohibido son válidos)
        self.assertIn(response.status_code, [302, 403])
        print_success("PERMISOS", "Usuario COMERCIAL es denegado correctamente")
    
    # ===== PRUEBAS DE URLs =====
    
    def test_export_budget_url_exists(self):
        """URL de presupuesto existe"""
        url = reverse('projects:export_budget_to_excel', args=[1])
        self.assertTrue(url.startswith('/projects/'))
        self.assertIn('export-budget-excel', url)
        print_success("URLS", f"URL presupuesto configurada: {url}")
    
    def test_export_gastos_url_exists(self):
        """URL de gastos existe"""
        url = reverse('projects:export_gastos_to_excel', args=[1])
        self.assertTrue(url.startswith('/projects/'))
        self.assertIn('export-gastos-excel', url)
        print_success("URLS", f"URL gastos configurada: {url}")
    
    def test_export_comparativo_url_exists(self):
        """URL de comparativo existe"""
        url = reverse('projects:export_comparativo_to_excel', args=[1])
        self.assertTrue(url.startswith('/projects/'))
        self.assertIn('export-comparativo-excel', url)
        print_success("URLS", f"URL comparativo configurada: {url}")
    
    # ===== PRUEBAS DE INTEGRIDAD =====
    
    def test_all_export_urls_configured(self):
        """Todas las URLs de exportación están configuradas"""
        urls = [
            'export_budget_to_excel',
            'export_gastos_to_excel',
            'export_comparativo_to_excel',
        ]
        configured_count = 0
        for url_name in urls:
            try:
                url = reverse(f'projects:{url_name}', args=[1])
                self.assertIsNotNone(url)
                configured_count += 1
            except Exception as e:
                self.fail(f"URL {url_name} no está configurada: {e}")
        print_success("INTEGRIDAD", f"Todas las URLs configuradas ({configured_count}/3)")
    
    def test_export_functions_exist(self):
        """Funciones de exportación existen en views"""
        from projects import views
        functions = [
            'export_budget_to_excel',
            'export_gastos_to_excel', 
            'export_comparativo_to_excel'
        ]
        for func_name in functions:
            self.assertTrue(hasattr(views, func_name))
        print_success("INTEGRIDAD", f"Todas las funciones existen en views ({len(functions)}/3)")


print("\n" + "="*70)
print("📊 PRUEBAS AUTOMÁTICAS - EXPORTACIÓN EXCEL")
print("="*70)
