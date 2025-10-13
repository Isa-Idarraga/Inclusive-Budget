"""Pure-Python unit tests for KPI numeric calculations (no Django, no DB).

These tests reimplement the numeric parts of `kpis_data` using plain Python
structures so they can run with `python -m unittest` without touching Django.
"""
import unittest
from dashboard.kpis import compute_kpis


class TestKpisNoDB(unittest.TestCase):
    def test_simple_totals_and_percentage(self):
        projects = [
            {'id': 1, 'name': 'A', 'presupuesto': 1000.0, 'presupuesto_gastado': 200.0},
            {'id': 2, 'name': 'B', 'presupuesto': 500.0, 'presupuesto_gastado': 250.0},
        ]
        materials = [
            {'id': 1, 'sku': 'M1', 'name': 'Mat1', 'stock': 5.0, 'presentation_qty': 100.0},
        ]

        res = compute_kpis(projects, materials)

        expected_total_presupuesto = 1500.0
        expected_total_gastado = 450.0
        expected_pct = round((expected_total_gastado / expected_total_presupuesto) * 100, 2)

        self.assertEqual(res['resumen_financiero']['total_presupuesto'], expected_total_presupuesto)
        self.assertEqual(res['resumen_financiero']['total_gastado'], expected_total_gastado)
        self.assertAlmostEqual(res['porcentaje_avance'], expected_pct)

    def test_material_low_stock_filter(self):
        projects = []
        materials = [
            {'id': 1, 'stock': 1.0, 'presentation_qty': 100.0},  # 1 <= 1.0 => should be low
            {'id': 2, 'stock': 50.0, 'presentation_qty': 100.0}, # 50 <= 1.0? no
        ]
        res = compute_kpis(projects, materials, material_threshold=1.0)
        self.assertEqual(len(res['materiales']), 1)
        self.assertEqual(res['materiales'][0]['id'], 1)

    def test_deviation_detection(self):
        projects = [
            {'id': 1, 'name': 'P1', 'presupuesto': 1000.0, 'presupuesto_gastado': 2000.0},
            {'id': 2, 'name': 'P2', 'presupuesto': 1000.0, 'presupuesto_gastado': 950.0},
        ]
        # deviation threshold 10% -> P1 has 200% (abs(200-100)=100 >=10) -> included
        res = compute_kpis(projects, [], desviacion_threshold=10.0)
        self.assertEqual(len(res['proyectos']), 1)
        self.assertEqual(res['proyectos'][0]['id'], 1)


if __name__ == '__main__':
    unittest.main()
