# projects/tests/test_utils_etapas.py
from django.test import TestCase
from decimal import Decimal
from projects.models import Project, BudgetSection, Material, ConsumoMaterial, ProjectBudgetItem, BudgetItem
from projects import utils

class GetEtapasConAvanceIntegrationTest(TestCase):
    def setUp(self):
        # 1) Crear proyecto
        self.project = Project.objects.create(
            name="Proyecto Test Integracion",
            creado_por=None  # ajusta si tu modelo requiere usuario; usa None si permite
        )

        # 2) Crear 3 secciones de ejemplo asociadas al proyecto (si tu flujo usa plantillas globales,
        #    en su lugar crea plantillas con project=None y los budget items lo referencian;
        #    este test usa secciones por proyecto para simular el caso básico)
        names = ["1. Terreno", "2. Cimentación", "3. Estructura"]
        for i, n in enumerate(names, start=1):
            BudgetSection.objects.create(
                project=self.project,
                name=n,
                order=i,
                description=f"Sección {i}"
            )

        # 3) Crear materiales con unit_cost (asegura que tu modelo Material tenga ese campo)
        self.mat_cemento = Material.objects.create(name="Cemento", unit_cost=Decimal("10.00"))
        self.mat_steel = Material.objects.create(name="Varilla", unit_cost=Decimal("5.00"))

        # 4) Crear consumos: asociar consumos a la primera y segunda sección
        s1 = self.project.budget_sections.get(order=1)
        s2 = self.project.budget_sections.get(order=2)

        ConsumoMaterial.objects.create(
            proyecto=self.project,
            etapa_presupuesto=s1,
            material=self.mat_cemento,
            cantidad_consumida=Decimal("100.0"),
            fecha_consumo="2025-01-01"
        )

        ConsumoMaterial.objects.create(
            proyecto=self.project,
            etapa_presupuesto=s2,
            material=self.mat_steel,
            cantidad_consumida=Decimal("50.0"),
            fecha_consumo="2025-01-02"
        )

        # 5) Crear ítems presupuestales (ProjectBudgetItem) para calcular 'presupuesto' si tu utils lo usa
        #    Este bloque asume existencia de modelos BudgetItem y ProjectBudgetItem con campos 'section', 'quantity', 'unit_price'.
        #    Ajusta nombres de campos según tu implementación real.
        # Primero crear BudgetItem (plantilla de ítem)
        b_item1 = BudgetItem.objects.create(name="Cemento 1", section=s1, unit_price=Decimal("10.00"))
        b_item2 = BudgetItem.objects.create(name="Varilla 1", section=s2, unit_price=Decimal("5.00"))

        # Luego vincular ProjectBudgetItem (cantidad) a proyecto
        ProjectBudgetItem.objects.create(project=self.project, budget_item=b_item1, quantity=Decimal("200"), unit_price=Decimal("10.00"))
        ProjectBudgetItem.objects.create(project=self.project, budget_item=b_item2, quantity=Decimal("100"), unit_price=Decimal("5.00"))

    def test_get_etapas_con_avance_returns_expected_structure_and_values(self):
        # Ejecutar la función
        resultado = utils.get_etapas_con_avance(self.project)

        # Es una lista con al menos 3 elementos (las secciones creadas)
        self.assertIsInstance(resultado, list)
        self.assertGreaterEqual(len(resultado), 3)

        # Buscar las etapas por nombre y comprobar que los gastos están calculados
        etapa1 = next((e for e in resultado if e["nombre"].startswith("1. Terreno")), None)
        etapa2 = next((e for e in resultado if e["nombre"].startswith("2. Cimentación")), None)

        self.assertIsNotNone(etapa1, "No se encontró la etapa 1 en el resultado")
        self.assertIsNotNone(etapa2, "No se encontró la etapa 2 en el resultado")

        # Gasto esperado: etapa1 -> 100 * 10 = 1000, etapa2 -> 50 * 5 = 250
        self.assertAlmostEqual(float(etapa1["gasto"]), 100.0 * 10.0, places=2)
        self.assertAlmostEqual(float(etapa2["gasto"]), 50.0 * 5.0, places=2)

        # El resultado debe contener las claves esperadas
        for e in [etapa1, etapa2]:
            self.assertIn("presupuesto", e)
            self.assertIn("gasto", e)
            self.assertIn("porcentaje", e)
            self.assertIn("estado", e)
