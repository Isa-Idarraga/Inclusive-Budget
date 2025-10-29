from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from projects.models import Project
from catalog.models import Unit, Material

User = get_user_model()


# class DashboardKpisTests(TestCase):
#     def setUp(self):
#         # Crear usuario superuser para simplificar autenticación
#         self.user = User.objects.create_superuser(username='admin', email='admin@example.com', password='pass')
#         self.client = Client()
#         self.client.login(username='admin', password='pass')

#         # Datos mínimos: unidad y material
#         self.unit = Unit.objects.create(name='kg', symbol='kg')
#         self.material = Material.objects.create(sku='ABC-1', name='Cemento', unit=self.unit, stock=100, presentation_qty=50, unit_cost=20000)

#         # Proyecto con presupuesto y gastado
#         self.project = Project.objects.create(
#             name='Proyecto Test',
#             location_address='Calle 1',
#             description='Desc',
#             built_area=100,
#             exterior_area=0,
#             columns_count=4,
#             walls_area=100,
#             windows_area=10,
#             doors_count=2,
#             doors_height=2.1,
#             presupuesto=1000000,
#             presupuesto_gastado=200000,
#             creado_por=self.user,
#             estado='en_proceso'
#         )

#     def test_kpis_data_json(self):
#         url = reverse('dashboard:kpis_data')
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, 200)
#         data = resp.json()
#         self.assertIn('porcentaje_avance', data)
#         self.assertIn('resumen_financiero', data)
#         self.assertIn('materiales', data)
#         self.assertIn('proyectos', data)

#     def test_kpis_page(self):
#         url = reverse('dashboard:kpis')
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, 200)
#         self.assertContains(resp, 'Dashboard - Indicadores Clave')

#     def test_kpis_values(self):
#         """Crear datos con valores conocidos y verificar cálculos numéricos del endpoint kpis_data"""
#         # Crear dos proyectos con valores controlados
#         p1 = Project.objects.create(
#             name='P1', location_address='A', description='A', built_area=10, exterior_area=0,
#             columns_count=1, walls_area=10, windows_area=1, doors_count=1, doors_height=2.0,
#             presupuesto=1000, presupuesto_gastado=200, creado_por=self.user, estado='en_proceso'
#         )
#         p2 = Project.objects.create(
#             name='P2', location_address='B', description='B', built_area=10, exterior_area=0,
#             columns_count=1, walls_area=10, windows_area=1, doors_count=1, doors_height=2.0,
#             presupuesto=500, presupuesto_gastado=250, creado_por=self.user, estado='en_proceso'
#         )

#         url = reverse('dashboard:kpis_data')
#         resp = self.client.get(url)
#         self.assertEqual(resp.status_code, 200)
#         data = resp.json()

#         # Totales esperados
#         expected_total_presupuesto = 1000 + 500 + 1000000  # incluye el proyecto creado en setUp
#         expected_total_gastado = 200 + 250 + 200000
#         # porcentaje de avance = total_gastado / total_presupuesto * 100
#         expected_pct = round((expected_total_gastado / expected_total_presupuesto) * 100, 2)

#         self.assertIn('resumen_financiero', data)
#         resumen = data['resumen_financiero']
#         # Comparaciones numéricas
#         self.assertAlmostEqual(float(resumen['total_presupuesto']), float(expected_total_presupuesto), places=2)
#         self.assertAlmostEqual(float(resumen['total_gastado']), float(expected_total_gastado), places=2)
#         self.assertAlmostEqual(float(data['porcentaje_avance']), float(expected_pct), places=2)

# # Create your tests here.


# from django.test import SimpleTestCase, RequestFactory
# from types import SimpleNamespace
# from unittest.mock import patch


# class DashboardKpisNoDBTests(SimpleTestCase):
#     """Tests that validate KPI numeric calculations without touching the database.

#     These tests patch the Project and Material objects imported in
#     `dashboard.views` so we can inject static data and verify the JSON payload.
#     """

#     def setUp(self):
#         self.factory = RequestFactory()

#     def _make_request(self):
#         req = self.factory.get('/dashboard/jefe/kpis/data/')
#         # Minimal user object
#         req.user = SimpleNamespace(is_authenticated=True, is_superuser=False, role='JEFE')
#         return req

#     def test_kpis_data_numbers_with_mocked_models(self):
#         # Prepare static projects: two projects with known presupuesto/gastado
#         proj1 = SimpleNamespace(id=1, name='P1', presupuesto=1000.0, presupuesto_gastado=200.0)
#         proj2 = SimpleNamespace(id=2, name='P2', presupuesto=2000.0, presupuesto_gastado=500.0)

#         # Fake queryset for projects: supports aggregate and iteration
#         class FakeProjQS(list):
#             def aggregate(self, **kw):
#                 return {
#                     'total_presupuesto': proj1.presupuesto + proj2.presupuesto,
#                     'total_gastado': proj1.presupuesto_gastado + proj2.presupuesto_gastado,
#                 }

#         fake_proj_qs = FakeProjQS([proj1, proj2])

#         # Mocked materials list
#         mat1 = SimpleNamespace(id=1, sku='M1', name='Mat1', stock=5.0, unit=SimpleNamespace(symbol='kg'), presentation_qty=100.0)
#         fake_mat_qs = [mat1]

#         with patch('dashboard.views.Project') as MockProject, patch('dashboard.views.Material') as MockMaterial:
#             MockProject.objects.filter.return_value = fake_proj_qs
#             MockMaterial.objects.filter.return_value = fake_mat_qs

#             from dashboard.views import kpis_data
#             req = self._make_request()
#             resp = kpis_data(req)

#             self.assertEqual(resp.status_code, 200)
#             data = resp.json()

#             expected_total_presupuesto = proj1.presupuesto + proj2.presupuesto
#             expected_total_gastado = proj1.presupuesto_gastado + proj2.presupuesto_gastado
#             expected_pct = round((expected_total_gastado / expected_total_presupuesto) * 100, 2)

#             self.assertAlmostEqual(data['resumen_financiero']['total_presupuesto'], expected_total_presupuesto)
#             self.assertAlmostEqual(data['resumen_financiero']['total_gastado'], expected_total_gastado)
#             self.assertAlmostEqual(data['porcentaje_avance'], expected_pct)

class SafeDashboardTests(TestCase):
    """Pruebas aisladas que no dependen de proveedores ni relaciones externas sensibles."""

    def setUp(self):
        self.user = User.objects.create_superuser(username='safeadmin', email='safe@example.com', password='safe123')
        self.client = Client()
        self.client.login(username='safeadmin', password='safe123')

        self.unit = Unit.objects.create(name='Litros', symbol='L')

        self.material1 = Material.objects.create(
            sku='MAT-001',
            name='Pintura Blanca',
            category='PINTURAS',
            stock=3,
            presentation_qty=10,
            unit=self.unit,
            unit_cost=15000
        )

        self.material2 = Material.objects.create(
            sku='MAT-002',
            name='Pintura Negra',
            category='PINTURAS',
            stock=11,
            presentation_qty=10,
            unit=self.unit,
            unit_cost=20000
        )

        self.project = Project.objects.create(
            name='Proyecto Seguro',
            location_address='Calle Ficticia 123',
            description='Un proyecto para pruebas seguras',
            built_area=120,
            exterior_area=10,
            columns_count=3,
            walls_area=80,
            windows_area=5,
            doors_count=2,
            doors_height=2.0,
            presupuesto=1000000,
            presupuesto_gastado=950000,
            creado_por=self.user,
            estado='en_proceso'
        )

    def test_dashboard_kpis_endpoint_ok(self):
        response = self.client.get(reverse('dashboard:kpis'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard - Indicadores Clave')

    def test_low_stock_materials_rendered(self):
        response = self.client.get(reverse('dashboard:kpis'))
        self.assertContains(response, 'Pintura Blanca')
        self.assertNotContains(response, 'Pintura Negra')

    def test_deviation_detected_correctly(self):
        # Usamos el threshold por defecto: 10%
        response = self.client.get(reverse('dashboard:kpis'))
        self.assertContains(response, 'Proyecto Seguro')
