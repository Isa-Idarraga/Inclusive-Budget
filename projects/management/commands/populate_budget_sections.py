from django.core.management.base import BaseCommand
from projects.models import BudgetSection, BudgetItem


class Command(BaseCommand):
    help = 'Poblar la base de datos con las 23 secciones del presupuesto detallado'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando población de secciones del presupuesto...'))
        
        # Datos de las secciones
        sections_data = [
            {
                'order': 1,
                'name': 'PRELIMINARES Y MANTENIMIENTOS',
                'description': 'Trabajos preliminares y mantenimientos necesarios para la obra',
                'items': [
                    {
                        'code': '1.1',
                        'description': 'Cerramiento provisional en madera y malla zarán (h=2.00 m)',
                        'unit': 'm',
                        'unit_price': 35000
                    },
                    {
                        'code': '1.2',
                        'description': 'Localización y replanteo',
                        'unit': 'm2',
                        'unit_price': 28000
                    },
                    {
                        'code': '1.3',
                        'description': 'Campamento en teleras con acometidas provisionales',
                        'unit': 'm2',
                        'unit_price': 250000
                    },
                    {
                        'code': '1.4',
                        'description': 'Descapote manual e≈50 cm',
                        'unit': 'm2',
                        'unit_price': 25000
                    }
                ]
            },
            {
                'order': 2,
                'name': 'EXCAVACIONES Y LLENOS',
                'description': 'Trabajos de excavación y llenos de material',
                'items': [
                    {
                        'code': '2.1',
                        'description': 'Excavación manual 0–2 m material heterogéneo',
                        'unit': 'm3',
                        'unit_price': 67692
                    },
                    {
                        'code': '2.2',
                        'description': 'Llenos compactados con sobrante de excavación',
                        'unit': 'm3',
                        'unit_price': 19806
                    },
                    {
                        'code': '2.4',
                        'description': 'Botada de material sobrante (cargue, transporte y disposición)',
                        'unit': 'm3',
                        'unit_price': 29812
                    },
                    {
                        'code': '2.5',
                        'description': 'Afirmado (suministro, riego y compactación)',
                        'unit': 'm3',
                        'unit_price': 120323
                    }
                ]
            },
            {
                'order': 3,
                'name': 'CIMENTACIONES',
                'description': 'Trabajos de cimentación y fundaciones',
                'items': [
                    {
                        'code': '3.1',
                        'description': 'Concreto ciclópeo (60% 21 MPa + 40% piedra de peña)',
                        'unit': 'm3',
                        'unit_price': 454470
                    },
                    {
                        'code': '3.2',
                        'description': 'Concreto 21 MPa para zapatas aisladas (sin refuerzo)',
                        'unit': 'm3',
                        'unit_price': 708829
                    },
                    {
                        'code': '3.4',
                        'description': 'Concreto 21 MPa para vigas de fundación (sin refuerzo)',
                        'unit': 'm3',
                        'unit_price': 1048550
                    }
                ]
            },
            {
                'order': 4,
                'name': 'ESTRUCTURA',
                'description': 'Estructura principal del edificio',
                'items': [
                    {
                        'code': '4.1',
                        'description': 'Concreto a la vista 28 MPa para columnas (sin refuerzo)',
                        'unit': 'm3',
                        'unit_price': 1026046
                    },
                    {
                        'code': '4.4',
                        'description': 'Losa maciza e=0.10 m (formaleta, vaciado y curado)',
                        'unit': 'm2',
                        'unit_price': 73469
                    },
                    {
                        'code': '4.5',
                        'description': 'Losa aligerada casetón recuperable e=0.30 m (sin acero)',
                        'unit': 'm2',
                        'unit_price': 238516
                    }
                ]
            },
            {
                'order': 5,
                'name': 'ACERO',
                'description': 'Acero de refuerzo para estructura',
                'items': [
                    {
                        'code': '5.1',
                        'description': 'Acero de refuerzo corrugado 6000 PSI (corte e instalación)',
                        'unit': 'kg',
                        'unit_price': 6101
                    },
                    {
                        'code': '5.2',
                        'description': 'Malla electrosoldada D-106 para losa de entrepiso',
                        'unit': 'm2',
                        'unit_price': 9401
                    }
                ]
            },
            {
                'order': 6,
                'name': 'MAMPOSTERÍA',
                'description': 'Trabajos de mampostería y muros',
                'items': [
                    {
                        'code': '6.1.2',
                        'description': 'Mampostería ladrillo 12×20×30 (e=12 cm) mortero 1:4',
                        'unit': 'M2',
                        'unit_price': 72803
                    },
                    {
                        'code': '6.3',
                        'description': 'Dovelas con barra 3/8" (incluye mortero y anclajes)',
                        'unit': 'm',
                        'unit_price': 18659
                    },
                    {
                        'code': '6.4',
                        'description': 'Anclajes con epóxico, barra 3/8" (prof. 10–30 cm)',
                        'unit': 'und',
                        'unit_price': 15485
                    },
                    {
                        'code': '6.5',
                        'description': 'Dintel concreto 21 MPa 12×15 cm',
                        'unit': 'm',
                        'unit_price': 53480
                    },
                    {
                        'code': '6.9',
                        'description': 'Lagrimal (suministro e instalación)',
                        'unit': 'm',
                        'unit_price': 23465
                    }
                ]
            },
            {
                'order': 7,
                'name': 'ESTUCOS, REVOQUES, PINTURAS, DRYWALL Y SUPERBOARD',
                'description': 'Acabados en muros y cielos',
                'items': [
                    {
                        'code': '7.2',
                        'description': 'Revoque exterior 1:4 con impermeabilizante',
                        'unit': 'm2',
                        'unit_price': 23042
                    },
                    {
                        'code': '7.2.1',
                        'description': 'Revoque interior 1:4',
                        'unit': 'm2',
                        'unit_price': 16971
                    },
                    {
                        'code': '7.3',
                        'description': 'Pintura vinilo interior, 3 manos (muros y cielos)',
                        'unit': 'm2',
                        'unit_price': 14046
                    },
                    {
                        'code': '7.3.1',
                        'description': 'Pintura acrílica exterior tipo koraza (NTC 1335)',
                        'unit': 'm2',
                        'unit_price': 19620
                    },
                    {
                        'code': '7.4.2',
                        'description': 'Cielo raso en Drywall (encintado y masillado)',
                        'unit': 'm2',
                        'unit_price': 62006
                    }
                ]
            },
            {
                'order': 8,
                'name': 'PISOS, ENCHAPES Y SÓCALOS',
                'description': 'Acabados de pisos y enchapes',
                'items': [
                    {
                        'code': '8.1',
                        'description': 'Piso porcelanato (incluye mortero, pegacor, boquilla)',
                        'unit': 'm2',
                        'unit_price': 153817
                    },
                    {
                        'code': '8.2.1',
                        'description': 'Enchape pared cerámica',
                        'unit': 'm2',
                        'unit_price': 101810
                    },
                    {
                        'code': '8.3',
                        'description': 'Piso SPC',
                        'unit': 'm2',
                        'unit_price': 148008
                    },
                    {
                        'code': '8.4.1',
                        'description': 'Guardaescobas en madera 14 cm',
                        'unit': 'm',
                        'unit_price': 21442
                    }
                ]
            },
            {
                'order': 9,
                'name': 'JUNTAS',
                'description': 'Juntas de dilatación y sellado',
                'items': [
                    {
                        'code': '9.1',
                        'description': 'Junta dilatación muro–estructura (sellador PU, Ø1" backer)',
                        'unit': 'm',
                        'unit_price': 26711
                    }
                ]
            },
            {
                'order': 10,
                'name': 'CARPINTERÍA METÁLICA Y VIDRIOS',
                'description': 'Carpintería metálica y vidrios',
                'items': [
                    {
                        'code': '10.1',
                        'description': 'Puerta vidriera monumental corrediza, vidrio templado 6 mm (2.17×2.4 m)',
                        'unit': 'un',
                        'unit_price': 3168000
                    },
                    {
                        'code': '10.3',
                        'description': 'Puerta vidriera monumental (3.81×2.4 m)',
                        'unit': 'un',
                        'unit_price': 5616000
                    },
                    {
                        'code': '10.8',
                        'description': 'Ventana corrediza aluminio 8025, vidrio 6 mm (1.40×1.18 m)',
                        'unit': 'un',
                        'unit_price': 588000
                    },
                    {
                        'code': '10.28',
                        'description': 'Escalera estructura metálica con pasos en madera',
                        'unit': 'Glb',
                        'unit_price': 12011740
                    }
                ]
            },
            {
                'order': 11,
                'name': 'CARPINTERÍA EN MADERA, MESONES Y ACCESORIOS',
                'description': 'Carpintería en madera y muebles',
                'items': [
                    {
                        'code': '11.2',
                        'description': 'Mueble bajo cocina RH 1.5 + mesón quarzstone',
                        'unit': 'm',
                        'unit_price': 878590
                    },
                    {
                        'code': '11.2.5',
                        'description': 'Torre de hornos RH 1.5 (cierre lento)',
                        'unit': 'un',
                        'unit_price': 929590
                    },
                    {
                        'code': '11.2.8',
                        'description': 'Mesón piedra sinterizada 60 cm + salpicadero 10 cm',
                        'unit': 'm',
                        'unit_price': 821990
                    },
                    {
                        'code': '11.6',
                        'description': 'Vestier en madera general 1.5 (cierre lento)',
                        'unit': 'm',
                        'unit_price': 422300
                    },
                    {
                        'code': '11.7',
                        'description': 'Mueble baño flotante RH 1.5 (0.80×0.55 m)',
                        'unit': 'un',
                        'unit_price': 2603990
                    },
                    {
                        'code': '11.8',
                        'description': 'Puerta en madera 0.70/0.80/0.90/1.00×2.40 m (con herrajes)',
                        'unit': 'un',
                        'unit_price': 900421
                    },
                    {
                        'code': '11.8.1',
                        'description': 'Puerta principal madera 2.00×3.89 m (chapa seguridad)',
                        'unit': 'un',
                        'unit_price': 2747590
                    },
                    {
                        'code': '11.8.3',
                        'description': 'Lavatrapero prefabricado 40×40',
                        'unit': 'un',
                        'unit_price': 236690
                    }
                ]
            },
            {
                'order': 12,
                'name': 'APARATOS SANITARIOS E INSTALACIONES HIDRÁULICAS',
                'description': 'Instalaciones hidráulicas y sanitarias',
                'items': [
                    {
                        'code': '12.1.1',
                        'description': 'Tubería sanitaria 4"',
                        'unit': 'm',
                        'unit_price': 36212
                    },
                    {
                        'code': '12.2',
                        'description': 'Caja de inspección 80×80',
                        'unit': 'un',
                        'unit_price': 583548
                    },
                    {
                        'code': '12.3',
                        'description': 'Sanitario Montecarlo Advance o similar (completo)',
                        'unit': 'un',
                        'unit_price': 700955
                    },
                    {
                        'code': '12.5',
                        'description': 'Ducha monocontrol Thames PRO SSB o similar',
                        'unit': 'un',
                        'unit_price': 437495
                    },
                    {
                        'code': '12.6',
                        'description': 'Tubería 1" agua potable',
                        'unit': 'M',
                        'unit_price': 21550
                    },
                    {
                        'code': '12.8',
                        'description': 'Tubería 1/2" agua potable',
                        'unit': 'm',
                        'unit_price': 14324
                    },
                    {
                        'code': '12.9',
                        'description': 'Tubería 1/2" agua caliente',
                        'unit': 'm',
                        'unit_price': 17938
                    },
                    {
                        'code': '12.12',
                        'description': 'Accesorios hidráulicos y sanitarios (global)',
                        'unit': 'GLB',
                        'unit_price': 4000000
                    }
                ]
            },
            {
                'order': 13,
                'name': 'INSTALACIONES ELÉCTRICAS Y REDES DE GAS',
                'description': 'Instalaciones eléctricas y de gas',
                'items': [
                    {
                        'code': '13.8.3',
                        'description': 'Toma doble 15A, 125V con polo a tierra (incluye caja 4×4")',
                        'unit': 'un',
                        'unit_price': 28051
                    },
                    {
                        'code': '13.10',
                        'description': 'Red de gas PEALPE 16 mm (accesorios incluidos)',
                        'unit': 'm',
                        'unit_price': 79205
                    }
                ]
            },
            {
                'order': 14,
                'name': 'CUBIERTAS',
                'description': 'Sistema de cubierta y estructura',
                'items': [
                    {
                        'code': '14.1',
                        'description': 'Cubierta panel inyectado CF 500 26/26 30 mm (incluye ruana/caballete/canoa/embudo)',
                        'unit': 'm2',
                        'unit_price': 257411
                    },
                    {
                        'code': '14.1.1',
                        'description': 'Estructura metálica de cubierta (perfiles, anclajes, pintura, montaje)',
                        'unit': 'glb',
                        'unit_price': 9035025
                    },
                    {
                        'code': '14.5',
                        'description': 'Pérgola metálica 7.67×1.10 m (zona social)',
                        'unit': 'un',
                        'unit_price': 4240590
                    }
                ]
            },
            {
                'order': 15,
                'name': 'ELECTRODOMÉSTICOS',
                'description': 'Electrodomésticos y equipos',
                'items': [
                    {
                        'code': '15.1',
                        'description': 'Estufa empotrable gas natural 4 puestos',
                        'unit': 'un',
                        'unit_price': 999690
                    },
                    {
                        'code': '15.3',
                        'description': 'Lavavajillas 12 puestos (suministro e instalación)',
                        'unit': 'un',
                        'unit_price': 2419690
                    },
                    {
                        'code': '15.5',
                        'description': 'Calentador paso gas natural 12 L',
                        'unit': 'un',
                        'unit_price': 2105490
                    }
                ]
            },
            {
                'order': 16,
                'name': 'IMPERMEABILIZACIONES',
                'description': 'Sistemas de impermeabilización',
                'items': [
                    {
                        'code': '16.1',
                        'description': 'Impermeabilización duchas/terrazas con broncoelástico',
                        'unit': 'm2',
                        'unit_price': 30201
                    }
                ]
            },
            {
                'order': 17,
                'name': 'PISOS EXTERIORES',
                'description': 'Pisos y acabados exteriores',
                'items': [
                    {
                        'code': '17.1',
                        'description': 'Adoquín bloque macizo gris 6×10×20 (incluye afirmado y arena)',
                        'unit': 'un',
                        'unit_price': 76735
                    }
                ]
            },
            {
                'order': 18,
                'name': 'LIMPIEZA GENERAL Y VIDRIOS',
                'description': 'Limpieza final y vidrios',
                'items': [
                    {
                        'code': '18.1',
                        'description': 'Limpieza general de entrega (incluye vidrios)',
                        'unit': 'gl',
                        'unit_price': 1500000
                    }
                ]
            },
            {
                'order': 19,
                'name': 'PAISAJISMO',
                'description': 'Trabajos de paisajismo y jardinería',
                'items': [
                    {
                        'code': '19.1',
                        'description': 'Grama tipo macana (conformación, nivelación y riego)',
                        'unit': 'gl',
                        'unit_price': 7500
                    }
                ]
            },
            {
                'order': 20,
                'name': 'SUPERVISIÓN Y CONTROL DE OBRA',
                'description': 'Supervisión y control de la obra',
                'items': [
                    {
                        'code': '20.2',
                        'description': 'Residente de obra',
                        'unit': 'mes',
                        'unit_price': 3333588
                    }
                ]
            },
            {
                'order': 21,
                'name': 'ADMINISTRACIÓN (12%)',
                'description': 'Gastos administrativos (12% sobre costo directo)',
                'is_percentage': True,
                'percentage_value': 12.00,
                'items': []
            },
            {
                'order': 22,
                'name': 'IMPUESTOS Y ESCRITURACIONES',
                'description': 'Impuestos y trámites legales',
                'items': [
                    {
                        'code': '22.1',
                        'description': 'Cargo fijo licencia',
                        'unit': '1',
                        'unit_price': 20053694
                    },
                    {
                        'code': '22.2',
                        'description': 'Escritura compra lote',
                        'unit': '1',
                        'unit_price': 3345800
                    }
                ]
            },
            {
                'order': 23,
                'name': 'ESTUDIOS Y DISEÑO',
                'description': 'Estudios técnicos y diseños',
                'items': [
                    {
                        'code': '23.1',
                        'description': 'Diseño arquitectónico',
                        'unit': '1',
                        'unit_price': 7497000
                    },
                    {
                        'code': '23.2',
                        'description': 'Estudio de suelos',
                        'unit': '1',
                        'unit_price': 2261000
                    },
                    {
                        'code': '23.3',
                        'description': 'Diseño estructural',
                        'unit': '1',
                        'unit_price': 1900000
                    },
                    {
                        'code': '23.4',
                        'description': 'Diseño eléctrico',
                        'unit': '1',
                        'unit_price': 1650000
                    },
                    {
                        'code': '23.7',
                        'description': 'Administración lote',
                        'unit': '8',
                        'unit_price': 545192
                    }
                ]
            }
        ]
        
        # Crear secciones e ítems
        for section_data in sections_data:
            # Crear o actualizar sección
            section, created = BudgetSection.objects.get_or_create(
                order=section_data['order'],
                defaults={
                    'name': section_data['name'],
                    'description': section_data['description'],
                    'is_percentage': section_data.get('is_percentage', False),
                    'percentage_value': section_data.get('percentage_value', 0)
                }
            )
            
            if created:
                self.stdout.write(f'✅ Sección creada: {section.name}')
            else:
                self.stdout.write(f'⚠️ Sección ya existe: {section.name}')
            
            # Crear ítems de la sección
            for item_data in section_data['items']:
                item, created = BudgetItem.objects.get_or_create(
                    section=section,
                    code=item_data['code'],
                    defaults={
                        'description': item_data['description'],
                        'unit': item_data['unit'],
                        'unit_price': item_data['unit_price'],
                        'order': len(section.items.all()) + 1
                    }
                )
                
                if created:
                    self.stdout.write(f'  ✅ Ítem creado: {item.code} - {item.description[:50]}...')
                else:
                    self.stdout.write(f'  ⚠️ Ítem ya existe: {item.code}')
        
        self.stdout.write(self.style.SUCCESS('✅ Población completada exitosamente!'))
        self.stdout.write(f'📊 Secciones creadas: {BudgetSection.objects.count()}')
        self.stdout.write(f'📋 Ítems creados: {BudgetItem.objects.count()}')
