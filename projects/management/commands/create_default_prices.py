from django.core.management.base import BaseCommand
from projects.models import UnitPrice, Project

class Command(BaseCommand):
    help = 'Crea precios unitarios por defecto para el sistema'

    def handle(self, *args, **options):
        # Precios base de construcción
        default_prices = [
            # Construcción básica
            {
                'category': 'construccion',
                'item_name': 'construccion_m2',
                'unit': 'm²',
                'price': 1500000,
                'description': 'Precio base por metro cuadrado construido'
            },
            
            # Factores de ubicación
            {
                'category': 'construccion',
                'item_name': 'factor_bogota',
                'unit': 'factor',
                'price': 1.15,
                'description': 'Factor multiplicador para proyectos en Bogotá (+15%)'
            },
            {
                'category': 'construccion',
                'item_name': 'factor_cali',
                'unit': 'factor',
                'price': 1.08,
                'description': 'Factor multiplicador para proyectos en Cali (+8%)'
            },
            
            # Factores de terreno
            {
                'category': 'terreno',
                'item_name': 'factor_terreno_rocoso',
                'unit': 'factor',
                'price': 1.20,
                'description': 'Factor por terreno rocoso (+20%)'
            },
            {
                'category': 'terreno',
                'item_name': 'factor_terreno_blando',
                'unit': 'factor',
                'price': 1.10,
                'description': 'Factor por terreno blando (+10%)'
            },
            
            # Factores de acceso
            {
                'category': 'terreno',
                'item_name': 'factor_acceso_dificil',
                'unit': 'factor',
                'price': 1.25,
                'description': 'Factor por acceso difícil (+25%)'
            },
            {
                'category': 'terreno',
                'item_name': 'factor_acceso_medio',
                'unit': 'factor',
                'price': 1.10,
                'description': 'Factor por acceso medio (+10%)'
            },
            
            # Factores de pisos
            {
                'category': 'estructura',
                'item_name': 'factor_segundo_piso',
                'unit': 'factor',
                'price': 1.30,
                'description': 'Factor por segundo piso (+30%)'
            },
            {
                'category': 'estructura',
                'item_name': 'factor_tres_pisos',
                'unit': 'factor',
                'price': 1.50,
                'description': 'Factor por tres o más pisos (+50%)'
            },
            
            # Acabados premium
            {
                'category': 'muros',
                'item_name': 'factor_acabado_premium',
                'unit': 'factor',
                'price': 1.40,
                'description': 'Factor por acabados premium (+40%)'
            },
            
            # Elementos adicionales
            {
                'category': 'pisos',
                'item_name': 'bano_adicional',
                'unit': 'unidad',
                'price': 8000000,
                'description': 'Costo por baño adicional completo'
            },
            {
                'category': 'carpinteria',
                'item_name': 'mueble_cocina_ml',
                'unit': 'ml',
                'price': 800000,
                'description': 'Costo por metro lineal de mueble de cocina'
            },
            
            # Exteriores
            {
                'category': 'exteriores',
                'item_name': 'adoquin_m2',
                'unit': 'm²',
                'price': 120000,
                'description': 'Costo por metro cuadrado de adoquín'
            },
            {
                'category': 'exteriores',
                'item_name': 'zonas_verdes_m2',
                'unit': 'm²',
                'price': 80000,
                'description': 'Costo por metro cuadrado de zonas verdes'
            },
            
            # Profesionales
            {
                'category': 'profesionales',
                'item_name': 'estudios_disenos',
                'unit': 'proyecto',
                'price': 15000000,
                'description': 'Costo de estudios y diseños profesionales'
            },
            {
                'category': 'profesionales',
                'item_name': 'licencia_impuestos',
                'unit': 'proyecto',
                'price': 8000000,
                'description': 'Costo de licencia e impuestos de construcción'
            },
        ]
        
        created_count = 0
        for price_data in default_prices:
            price, created = UnitPrice.objects.get_or_create(
                item_name=price_data['item_name'],
                defaults=price_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Creado: {price_data["item_name"]} - ${price_data["price"]:,.0f}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {created_count} precios unitarios por defecto.')
        )
