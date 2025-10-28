from django.db import models
from django.conf import settings  # Para usar el modelo de usuario personalizado
from django.core.validators import MinValueValidator
from catalog.models import Material, Supplier
from django.db.models import F
from django.core.validators import MinValueValidator
from django.db import transaction
from django.db.models import Sum, F, DecimalField, ExpressionWrapper


# MODELOS DE ROLES Y TRABAJADORES


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del rol")
    description = models.TextField(blank=True, verbose_name="Descripción")
    salario_base_dia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Salario base por día (COP)",
        default=0,
    )

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return f"{self.name} (${self.salario_base_dia:,.0f}/día)"


class Worker(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre del trabajador")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    cedula = models.CharField(max_length=20, verbose_name="Cédula")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, verbose_name="Rol"
    )

    class Meta:
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"

    def __str__(self):
        return self.name


class UnitPrice(models.Model):
    """
    Modelo para manejar precios unitarios desde el admin
    Permite actualizar precios sin modificar código
    """

    # Categorías de precios
    CATEGORY_CHOICES = [
        ("construccion", "Construcción"),
        ("terreno", "Terreno y Preliminares"),
        ("estructura", "Estructura y Cimentación"),
        ("muros", "Muros y Acabados"),
        ("pisos", "Pisos y Enchapes"),
        ("carpinteria", "Carpinterías"),
        ("hidro", "Hidrosanitario"),
        ("electrico", "Instalaciones Eléctricas"),
        ("cubierta", "Cubierta e Impermeabilización"),
        ("exteriores", "Exteriores y Paisajismo"),
        ("profesionales", "Indirectos y Profesionales"),
    ]

    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, verbose_name="Categoría"
    )
    item_name = models.CharField(max_length=200, verbose_name="Nombre del ítem")
    unit = models.CharField(
        max_length=50, verbose_name="Unidad", help_text="Ej: m², unidad, ml"
    )
    price = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Precio unitario"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Precio Unitario"
        verbose_name_plural = "Precios Unitarios"
        ordering = ["category", "item_name"]

    def __str__(self):
        return f"{self.item_name} - ${self.price:,.0f}/{self.unit}"


class Project(models.Model):
    """
    Modelo Project - Configurado para PostgreSQL
    Este modelo almacena toda la información de los proyectos de construcción
    y se mapea a tablas PostgreSQL con tipos de datos optimizados
    """

    # ===== OPCIONES PARA SELECTS =====

    # Estados del proyecto
    ESTADO_CHOICES = [
        ("en_proceso", "En Proceso"),
        ("terminado", "Terminado"),
        ("futuro", "Futuro"),
    ]

    # 1. Datos generales
    UBICACION_CHOICES = [
        ("Medellin", "Medellín"),
        ("Bogota", "Bogotá"),
        ("Cali", "Cali"),
        ("Otra", "Otra (especificar)"),
    ]

    PISOS_CHOICES = [
        ("1", "1 piso"),
        ("2", "2 pisos"),
        ("3_mas", "3 o más"),
    ]

    # 2. Terreno y preliminares
    TERRENO_CHOICES = [
        ("blando", "Suelo blando / relleno"),
        ("normal", "Suelo normal (tierra firme)"),
        ("rocoso", "Suelo rocoso"),
    ]

    ACCESO_CHOICES = [
        ("facil", "Fácil (camiones entran sin problema)"),
        ("medio", "Medio (calles angostas / pendientes)"),
        ("dificil", "Difícil (solo vehículos pequeños, acarreos)"),
    ]

    # 3. Estructura
    ENTREPISO_CHOICES = [
        ("maciza", "Losa maciza"),
        ("aligerada", "Losa aligerada (casetón recuperable)"),
    ]

    EXIGENCIA_CHOICES = [
        ("normal", "Normal (residencial estándar)"),
        ("alta", "Alta (sísmica / cargas especiales)"),
    ]

    # 4. Muros y acabados
    RELACION_MUROS_CHOICES = [
        ("baja", "Baja (mucho espacio abierto, pocos muros internos)"),
        ("media", "Media (distribución típica de vivienda)"),
        ("alta", "Alta (muchos muros divisorios y fachadas)"),
    ]

    ACABADO_MUROS_CHOICES = [
        ("basico", "Básico (pintura sencilla, 1–2 manos)"),
        ("estandar", "Estándar (estuco + pintura 2–3 manos)"),
        ("premium", "Premium (estuco fino + pintura o acabados especiales)"),
    ]

    CIELORRASOS_CHOICES = [
        ("ninguno", "Ninguno (concreto visto)"),
        ("parcial", "Drywall parcial (zonas sociales y baños)"),
        ("total", "Drywall total"),
    ]

    # 5. Pisos
    PISO_CHOICES = [
        ("ceramica", "Cerámica básica"),
        ("porcelanato", "Porcelanato estándar"),
        ("spc", "SPC o laminado"),
    ]

    ENCHAPE_CHOICES = [
        ("bajo", "Bajo (1.5 m de altura)"),
        ("medio", "Medio (2.1 m aprox.)"),
        ("total", "Total (hasta techo)"),
    ]

    # 6. Carpinterías
    VENTANAS_CHOICES = [
        ("bajo", "Bajo (10%)"),
        ("medio", "Medio (20%)"),
        ("alto", "Alto (30%)"),
    ]

    CLOSETS_CHOICES = [
        ("ninguno", "Ninguno"),
        ("basico", "Básico (1–2 módulos)"),
        ("amplio", "Amplio (vestier completo)"),
    ]

    # 8. Instalaciones eléctricas
    DOTACION_ELECTRICA_CHOICES = [
        ("basico", "Básico (mínimo normativo)"),
        ("estandar", "Estándar (más puntos de tomas y luminarias)"),
        ("premium", "Premium (domótica o iluminación decorativa)"),
    ]

    # 9. Cubierta
    CUBIERTA_CHOICES = [
        ("tradicional", "Teja tradicional (fibrocemento, zinc)"),
        ("panel", "Panel inyectado (térmico)"),
    ]

    # ===== INFORMACIÓN BÁSICA DEL PROYECTO =====
    # PostgreSQL: VARCHAR(200) - Campo de texto con límite de caracteres
    name = models.CharField(max_length=200, verbose_name="Nombre del proyecto")
    workers = models.ManyToManyField(
        Worker,
        blank=True,
        related_name="projects",
        verbose_name="Trabajadores asignados",
    )

    # PostgreSQL: TEXT - Campo de texto sin límite para direcciones largas
    location_address = models.TextField(verbose_name="Dirección ubicación")

    # PostgreSQL: TEXT - Campo de texto sin límite para descripciones detalladas
    description = models.TextField(verbose_name="Descripción")

    # ===== MEDIDAS Y DIMENSIONES =====
    # PostgreSQL: NUMERIC(10,2) - Número decimal con 10 dígitos totales, 2 decimales
    # Perfecto para metros cuadrados con precisión de centímetros
    built_area = models.DecimalField(
        max_digits=10,  # Total de dígitos (incluyendo decimales)
        decimal_places=2,  # Número de decimales
        verbose_name="Metros² de construido (casa)",
        validators=[MinValueValidator(0)],  # Validación: no puede ser negativo
    )

    # PostgreSQL: NUMERIC(10,2) - Mismo formato que built_area
    exterior_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Metros² de exteriores",
        validators=[MinValueValidator(0)],
    )

    # PostgreSQL: INTEGER - Número entero para contar columnas
    columns_count = models.IntegerField(
        verbose_name="Número de columnas", validators=[MinValueValidator(0)]
    )

    # PostgreSQL: NUMERIC(10,2) - Para áreas de paredes
    walls_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Metros² de paredes",
        validators=[MinValueValidator(0)],
    )

    # PostgreSQL: NUMERIC(10,2) - Para áreas de ventanas
    windows_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Metros² de ventanas",
        validators=[MinValueValidator(0)],
    )

    # PostgreSQL: INTEGER - Número entero para contar puertas
    doors_count = models.IntegerField(
        verbose_name="Número de puertas", validators=[MinValueValidator(0)]
    )

    # PostgreSQL: NUMERIC(5,2) - Para alturas con precisión de centímetros
    doors_height = models.DecimalField(
        max_digits=5,  # Menos dígitos porque las alturas son menores
        decimal_places=2,
        default=2.10,
        verbose_name="Altura de las puertas (en metros)",
        validators=[MinValueValidator(0)],
    )

    # ===== PRESUPUESTO Y ESTADO =====
    # PostgreSQL: NUMERIC(15,2) - Para presupuestos grandes con precisión de centavos
    # 15 dígitos permiten presupuestos de hasta 999,999,999,999.99
    presupuesto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Presupuesto total",
        default=0,
        validators=[MinValueValidator(0)]

        
    )

    # PostgreSQL: NUMERIC(15,2) - Mismo formato que presupuesto
    presupuesto_gastado = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Presupuesto gastado",
        default=0,
        validators=[MinValueValidator(0)],
    )

    # PostgreSQL: VARCHAR(20) - Campo de texto para el estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,  # Restringe los valores a las opciones definidas
        default="futuro",
        verbose_name="Estado del proyecto",
    )

    @property
    def presupuesto_actual(self):
        return self.presupuesto - self.presupuesto_gastado_calculado

    @property
    def presupuesto_gastado_calculado(self):
    
        total = (
            EntradaMaterial.objects
            .filter(proyecto=self)
            .annotate(
                costo=ExpressionWrapper(
                    F("cantidad") * F("material__unit_cost"),
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
            .aggregate(total=Sum("costo"))["total"]
        )
        return total or 0
    
    # ===== NUEVOS CAMPOS DEL CUESTIONARIO DETALLADO =====

    # 1. Datos generales del proyecto
    ubicacion_proyecto = models.CharField(
        max_length=20,
        choices=UBICACION_CHOICES,
        verbose_name="Ubicación del proyecto",
        default="medellin",
    )
    otra_ubicacion = models.CharField(
        max_length=200, blank=True, verbose_name="Otra ubicación (especificar)"
    )
    area_construida_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Área construida total (m²)",
        validators=[MinValueValidator(0)],
        default=0,
    )
    numero_pisos = models.CharField(
        max_length=10,
        choices=PISOS_CHOICES,
        verbose_name="Número de pisos",
        default="1",
    )
    area_exterior_intervenir = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Área exterior a intervenir (m²)",
        validators=[MinValueValidator(0)],
        default=0,
    )

    # 2. Terreno y preliminares
    tipo_terreno = models.CharField(
        max_length=20,
        choices=TERRENO_CHOICES,
        verbose_name="Tipo de terreno predominante",
        default="normal",
    )
    acceso_obra = models.CharField(
        max_length=20,
        choices=ACCESO_CHOICES,
        verbose_name="Acceso a la obra",
        default="facil",
    )
    requiere_cerramiento = models.BooleanField(
        default=False, verbose_name="¿Requiere cerramiento provisional?"
    )

    # 3. Estructura y cimentación
    sistema_entrepiso = models.CharField(
        max_length=20,
        choices=ENTREPISO_CHOICES,
        verbose_name="Sistema de entrepiso / losa",
        default="maciza",
    )
    exigencia_estructural = models.CharField(
        max_length=20,
        choices=EXIGENCIA_CHOICES,
        verbose_name="Nivel de exigencia estructural",
        default="normal",
    )

    # 4. Muros y acabados básicos
    relacion_muros = models.CharField(
        max_length=20,
        choices=RELACION_MUROS_CHOICES,
        verbose_name="Relación muros / área construida",
        default="media",
    )
    acabado_muros = models.CharField(
        max_length=20,
        choices=ACABADO_MUROS_CHOICES,
        verbose_name="Acabado de muros interiores",
        default="estandar",
    )
    cielorrasos = models.CharField(
        max_length=20,
        choices=CIELORRASOS_CHOICES,
        verbose_name="Cielorrasos",
        default="parcial",
    )

    # 5. Pisos y enchapes
    piso_zona_social = models.CharField(
        max_length=20,
        choices=PISO_CHOICES,
        verbose_name="Tipo de piso en zona social",
        default="ceramica",
    )
    piso_habitaciones = models.CharField(
        max_length=20,
        choices=PISO_CHOICES,
        verbose_name="Tipo de piso en habitaciones",
        default="ceramica",
    )
    numero_banos = models.IntegerField(
        verbose_name="Número de baños completos",
        validators=[MinValueValidator(0)],
        default=1,
    )
    nivel_enchape_banos = models.CharField(
        max_length=20,
        choices=ENCHAPE_CHOICES,
        verbose_name="Nivel de enchape en baños",
        default="medio",
    )

    # 6. Carpinterías
    puertas_interiores = models.IntegerField(
        verbose_name="Cantidad de puertas interiores",
        validators=[MinValueValidator(0)],
        default=0,
    )
    puerta_principal_especial = models.BooleanField(
        default=False, verbose_name="¿Puerta principal especial?"
    )
    porcentaje_ventanas = models.CharField(
        max_length=20,
        choices=VENTANAS_CHOICES,
        verbose_name="Porcentaje aproximado de fachada en ventanas",
        default="medio",
    )
    metros_mueble_cocina = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Cocina – metros lineales de mueble bajo",
        validators=[MinValueValidator(0)],
        default=0,
    )
    vestier_closets = models.CharField(
        max_length=20,
        choices=CLOSETS_CHOICES,
        verbose_name="Vestier o closets",
        default="ninguno",
    )

    # 7. Hidrosanitario
    calentador_gas = models.BooleanField(
        default=False, verbose_name="¿Tendrá calentador de agua a gas?"
    )
    incluye_lavadero = models.BooleanField(
        default=False, verbose_name="¿Incluye lavadero / zona de ropas?"
    )
    punto_lavaplatos = models.BooleanField(
        default=False, verbose_name="Punto lavaplatos"
    )
    punto_lavadora = models.BooleanField(default=False, verbose_name="Punto lavadora")
    punto_lavadero = models.BooleanField(default=False, verbose_name="Punto lavadero")

    # 8. Instalaciones eléctricas y gas
    dotacion_electrica = models.CharField(
        max_length=20,
        choices=DOTACION_ELECTRICA_CHOICES,
        verbose_name="Nivel de dotación eléctrica",
        default="estandar",
    )
    red_gas_natural = models.BooleanField(
        default=False, verbose_name="¿Incluye red de gas natural?"
    )

    # 9. Cubierta e impermeabilización
    tipo_cubierta = models.CharField(
        max_length=20,
        choices=CUBIERTA_CHOICES,
        verbose_name="Tipo de cubierta",
        default="tradicional",
    )
    impermeabilizacion_adicional = models.BooleanField(
        default=False, verbose_name="¿Requiere impermeabilización adicional?"
    )

    # 10. Exteriores y paisajismo
    area_adoquin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Área aproximada de adoquín exterior (m²)",
        validators=[MinValueValidator(0)],
        default=0,
    )
    area_zonas_verdes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Área aproximada de zonas verdes (m²)",
        validators=[MinValueValidator(0)],
        default=0,
    )

    # 11. Indirectos y profesionales
    incluir_estudios_disenos = models.BooleanField(
        default=False, verbose_name="¿Incluir costos de estudios y diseños?"
    )
    incluir_licencia_impuestos = models.BooleanField(
        default=False, verbose_name="¿Incluir costos de licencia e impuestos?"
    )

    # ===== IMAGEN DEL PROYECTO =====
    # PostgreSQL: VARCHAR - Almacena la ruta del archivo
    # El archivo físico se guarda en el sistema de archivos
    imagen_proyecto = models.ImageField(
        upload_to="imagenes_proyectos/",  # Subcarpeta donde se guardan las imágenes
        verbose_name="Imagen del proyecto",
        blank=True,  # Permite que el campo esté vacío
        null=True,  # Permite NULL en la base de datos
    )

    # ===== RELACIÓN CON USUARIO =====
    # PostgreSQL: INTEGER + FOREIGN KEY - Clave foránea al modelo de usuario
    # Usa settings.AUTH_USER_MODEL para el modelo de usuario personalizado
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Apunta al modelo User personalizado
        on_delete=models.CASCADE,  # Si se elimina el usuario, se elimina el proyecto
        verbose_name="Creado por",
    )
    created_by_ai = models.BooleanField(
        default=False,
        verbose_name="Creado por IA",
        help_text="Indica si este proyecto fue generado automáticamente por el chatbot IA"
    )   

    # ===== FECHAS =====
    # PostgreSQL: TIMESTAMP - Fecha y hora de creación (se establece automáticamente)
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,  # Se establece solo al crear
        verbose_name="Fecha de creación",
    )

    # PostgreSQL: TIMESTAMP - Fecha y hora de última actualización (se actualiza automáticamente)
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,  # Se actualiza cada vez que se guarda
        verbose_name="Última actualización",
    )

    # ===== CONFIGURACIÓN DEL MODELO =====
    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = [
            "-fecha_creacion"
        ]  # Ordena por fecha de creación descendente (más recientes primero)

    def __str__(self):
        """Representación en string del proyecto (para admin y shell)"""
        return self.name

    def calculate_legacy_fields(self):
        """
        Calcula campos heredados basados en datos del proyecto
        Estos campos se usan para compatibilidad con sistemas legacy
        """
        from decimal import Decimal

        # 1. Área construida total (si no existe)
        if not self.area_construida_total or self.area_construida_total == 0:
            self.area_construida_total = self.built_area or Decimal("0")

        # 2. Área exterior a intervenir (si no existe)
        if not self.area_exterior_intervenir or self.area_exterior_intervenir == 0:
            self.area_exterior_intervenir = self.exterior_area or Decimal("0")

        # 3. Número de columnas (si no existe)
        if not self.columns_count or self.columns_count == 0:
            # Calcular columnas basado en área (aproximadamente 1 columna cada 25m²)
            area = float(self.area_construida_total or 0)
            self.columns_count = max(4, int(area / 25))  # Mínimo 4 columnas

        # 4. Área de paredes (si no existe)
        if not self.walls_area or self.walls_area == 0:
            # Calcular área de paredes basado en área construida y altura
            area = float(self.area_construida_total or 0)
            altura_pared = 2.7  # Altura estándar de pared
            perimetro = (area**0.5) * 4  # Perímetro aproximado
            self.walls_area = Decimal(str(perimetro * altura_pared))

        # 5. Área de ventanas (si no existe)
        if not self.windows_area or self.windows_area == 0:
            # Calcular área de ventanas (aproximadamente 15% del área de paredes)
            area_paredes = float(self.walls_area or 0)
            self.windows_area = Decimal(str(area_paredes * 0.15))

        # 6. Número de puertas (si no existe)
        if not self.doors_count or self.doors_count == 0:
            # Priorizar el valor del formulario puertas_interiores
            if self.puertas_interiores and self.puertas_interiores > 0:
                self.doors_count = self.puertas_interiores
            else:
                # Calcular puertas basado en área (aproximadamente 1 puerta cada 30m²)
                area = float(self.area_construida_total or 0)
                self.doors_count = max(2, int(area / 30))  # Mínimo 2 puertas

        # 7. Altura de puertas (si no existe)
        if not self.doors_height or self.doors_height == 0:
            self.doors_height = Decimal("2.1")  # Altura estándar de puerta

        # 8. Área de mueble de cocina (si no existe)
        if not self.metros_mueble_cocina or self.metros_mueble_cocina == 0:
            # Calcular metros lineales de cocina (aproximadamente 6m para cocina estándar)
            self.metros_mueble_cocina = Decimal("6.0")

        # 9. Área de adoquín (si no existe)
        if not self.area_adoquin or self.area_adoquin == 0:
            # Calcular área de adoquín (aproximadamente 20% del área exterior)
            area_exterior = float(self.area_exterior_intervenir or 0)
            self.area_adoquin = Decimal(str(area_exterior * 0.2))

        # 10. Área de zonas verdes (si no existe)
        if not self.area_zonas_verdes or self.area_zonas_verdes == 0:
            # Calcular área de zonas verdes (aproximadamente 30% del área exterior)
            area_exterior = float(self.area_exterior_intervenir or 0)
            self.area_zonas_verdes = Decimal(str(area_exterior * 0.3))

    # ===== PROPIEDADES CALCULADAS =====
    @property
    def presupuesto_restante(self):
        """
        Calcula el presupuesto restante
        PostgreSQL: Se calcula en Python, no en la base de datos
        """
        return self.presupuesto - self.presupuesto_gastado

    @property
    def porcentaje_presupuesto(self):
        """
        Calcula el porcentaje del presupuesto gastado
        PostgreSQL: Se calcula en Python, no en la base de datos
        """
        if self.presupuesto > 0:
            return (self.presupuesto_gastado / self.presupuesto) * 100
        return 0

    def calculate_detailed_budget(self):
        """
        Calcula presupuesto detallado usando precios unitarios del admin
        """
        total = 0

        try:
            # Obtener precios unitarios activos
            precios = {
                item.item_name: item.price
                for item in UnitPrice.objects.filter(is_active=True)
            }

            # 1. Construcción básica por m²
            if "construccion_m2" in precios:
                total += float(self.area_construida_total) * float(
                    precios["construccion_m2"]
                )

            # 2. Factores de ubicación
            if self.ubicacion_proyecto == "bogota" and "factor_bogota" in precios:
                total *= float(precios["factor_bogota"])
            elif self.ubicacion_proyecto == "cali" and "factor_cali" in precios:
                total *= float(precios["factor_cali"])

            # 3. Factores de terreno
            if self.tipo_terreno == "rocoso" and "factor_terreno_rocoso" in precios:
                total *= float(precios["factor_terreno_rocoso"])
            elif self.tipo_terreno == "blando" and "factor_terreno_blando" in precios:
                total *= float(precios["factor_terreno_blando"])

            # 4. Factores de acceso
            if self.acceso_obra == "dificil" and "factor_acceso_dificil" in precios:
                total *= float(precios["factor_acceso_dificil"])
            elif self.acceso_obra == "medio" and "factor_acceso_medio" in precios:
                total *= float(precios["factor_acceso_medio"])

            # 5. Pisos adicionales
            if self.numero_pisos == "2" and "factor_segundo_piso" in precios:
                total *= float(precios["factor_segundo_piso"])
            elif self.numero_pisos == "3_mas" and "factor_tres_pisos" in precios:
                total *= float(precios["factor_tres_pisos"])

            # 6. Acabados premium
            if self.acabado_muros == "premium" and "factor_acabado_premium" in precios:
                total *= float(precios["factor_acabado_premium"])

            # 7. Elementos adicionales
            if self.numero_banos > 1 and "bano_adicional" in precios:
                total += (self.numero_banos - 1) * float(precios["bano_adicional"])

            if self.metros_mueble_cocina > 0 and "mueble_cocina_ml" in precios:
                total += float(self.metros_mueble_cocina) * float(
                    precios["mueble_cocina_ml"]
                )

            # 8. Exteriores
            if self.area_adoquin > 0 and "adoquin_m2" in precios:
                total += float(self.area_adoquin) * float(precios["adoquin_m2"])

            if self.area_zonas_verdes > 0 and "zonas_verdes_m2" in precios:
                total += float(self.area_zonas_verdes) * float(
                    precios["zonas_verdes_m2"]
                )

            # 9. Profesionales
            if self.incluir_estudios_disenos and "estudios_disenos" in precios:
                total += float(precios["estudios_disenos"])

            if self.incluir_licencia_impuestos and "licencia_impuestos" in precios:
                total += float(precios["licencia_impuestos"])

        except Exception as e:
            # Si hay error, usar cálculo básico
            total = (
                float(self.area_construida_total) * 1500000
                if self.area_construida_total
                else 0
            )

        return int(total)

    def has_detailed_budget_items(self):
        """
        Verifica si el proyecto tiene ítems de presupuesto detallado configurados
        """
        return self.budget_items.exists()

    def calculate_final_budget(self):
        """
        Calcula el presupuesto final del proyecto
        Si tiene ítems detallados, usa el cálculo detallado
        Si no, usa el cálculo tradicional
        """
        from decimal import Decimal
        from django.db.models import Sum, Q
        from decimal import Decimal

        if self.has_detailed_budget_items():
                # Cálculo detallado con ítems específicos
                totals = self.budget_items.select_related('budget_item__section').aggregate(
                    costo_directo=Sum('total_price', filter=~Q(budget_item__section__order=21)),
                    administracion_manual=Sum('total_price', filter=Q(budget_item__section__order=21))
                )
                costo_directo = totals['costo_directo'] or Decimal('0')
                administracion_manual = totals['administracion_manual'] or Decimal('0')
                administracion_automatica = costo_directo * Decimal('0.12')
                total = costo_directo + administracion_automatica + administracion_manual
        else:
                # Cálculo tradicional
                total = self.calculate_detailed_budget()

            # Aseguramos un mínimo razonable
        if not total or total <= 0:
                total = Decimal('1000000')

        return total
 #Modelos de proveeddores entradas y materiales

class EntradaMaterial(models.Model):
    proyecto = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="entradas",
        verbose_name="Proyecto"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="entradas",
        verbose_name="Material"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad ingresada")
    lote = models.CharField(max_length=50, verbose_name="Número de lote")
    proveedor = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Proveedor"
    )
    fecha_ingreso = models.DateField(verbose_name="Fecha de ingreso")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Entrada de material"
        verbose_name_plural = "Entradas de materiales"
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"{self.material.name} +{self.cantidad} (Lote {self.lote})"

    def save(self, *args, **kwargs):
        """
        Cuando se crea o edita una entrada:
        - Si es nueva: aumenta stock
        - Si se edita: ajusta stock en base a la diferencia
        """
        with transaction.atomic():
            if self.pk:  
                # Si ya existe, calculamos la diferencia
                old = EntradaMaterial.objects.get(pk=self.pk)
                diferencia = self.cantidad - old.cantidad
            else:
                # Si es nuevo, la diferencia es la cantidad completa
                diferencia = self.cantidad

            super().save(*args, **kwargs)

            if diferencia != 0:
                # Actualizar stock global
                Material.objects.filter(pk=self.material.pk).update(
                    stock=F("stock") + diferencia
                )

                # Actualizar stock por proyecto
                pm, _ = ProyectoMaterial.objects.get_or_create(
                    proyecto=self.proyecto,
                    material=self.material,
                    defaults={"stock_proyecto": 0}
                )
                pm.stock_proyecto = F("stock_proyecto") + diferencia
                pm.save()

    def delete(self, *args, **kwargs):
        """
        Al eliminar una entrada de material, descontar del stock
        """
        with transaction.atomic():
            # Descontar del stock global
            Material.objects.filter(pk=self.material.pk).update(
                stock=F("stock") - self.cantidad
            )

            # Descontar del stock del proyecto
            try:
                pm = ProyectoMaterial.objects.select_for_update().get(
                    proyecto=self.proyecto,
                    material=self.material
                )
                pm.stock_proyecto = F("stock_proyecto") - self.cantidad
                pm.save()
                pm.refresh_from_db()
            except ProyectoMaterial.DoesNotExist:
                pass  # Si no existe la relación, solo eliminar la entrada

            # Eliminar la entrada
            super().delete(*args, **kwargs)


# STOCK POR PROYECTO
class ProyectoMaterial(models.Model):
    proyecto = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="materiales"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="proyectos"
    )
    stock_proyecto = models.DecimalField(
        "Stock asignado al proyecto",
        max_digits=12,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ("proyecto", "material")

    def __str__(self):
        return f"{self.material.name} en {self.proyecto.name} → {self.stock_proyecto}"


# CONSUMO DIARIO DE MATERIALES (RF17A)
class ConsumoMaterial(models.Model):
    """
    Modelo para registrar el consumo diario de materiales en un proyecto
    Permite documentar el uso de recursos con fecha específica
    """
    proyecto = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="consumos",
        verbose_name="Proyecto"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="consumos",
        verbose_name="Material"
    )
    cantidad_consumida = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        verbose_name="Cantidad consumida",
        validators=[MinValueValidator(0.001)],
        help_text="Cantidad del material que se consumió"
    )
    fecha_consumo = models.DateField(
        verbose_name="Fecha de consumo",
        help_text="Fecha en la que se usó el material"
    )
    componente_actividad = models.CharField(
        max_length=200,
        verbose_name="Componente/Actividad",
        help_text="Ej: Cimentación, Muros primer piso, Instalación eléctrica"
    )


    etapa_presupuesto = models.ForeignKey(
        'BudgetSection',
        on_delete=models.PROTECT,
        related_name="consumos_materiales",
        verbose_name="Etapa del presupuesto",
        help_text="Etapa/categoría del presupuesto detallado",
        null=True,  # Para consumos antiguos
        blank=False  # Obligatorio en formularios nuevos
    )
    responsable = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Responsable del uso",
        help_text="Nombre de la persona responsable del uso del material"
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Notas adicionales sobre el consumo (opcional)"
    )

    # Campos de auditoría
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Registrado por",
        help_text="Usuario que registró este consumo",
        blank=True,
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro",
        help_text="Fecha y hora en que se registró este consumo en el sistema"
    )
    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización",
    )

    class Meta:
        verbose_name = "Consumo de material"
        verbose_name_plural = "Consumos de materiales"
        ordering = ["-fecha_consumo", "-fecha_registro"]
        indexes = [
            models.Index(fields=['proyecto', 'fecha_consumo']),
            models.Index(fields=['material', 'fecha_consumo']),
        ]

    def __str__(self):
        return f"{self.material.name} - {self.cantidad_consumida} ({self.fecha_consumo})"

    def clean(self):
        """Validación a nivel de modelo"""
        from django.core.exceptions import ValidationError

        if self.cantidad_consumida and self.cantidad_consumida <= 0:
            raise ValidationError({
                'cantidad_consumida': 'La cantidad consumida debe ser mayor a cero.'
            })

        # Validar que la fecha de consumo no sea futura
        from django.utils import timezone
        if self.fecha_consumo and self.fecha_consumo > timezone.now().date():
            raise ValidationError({
                'fecha_consumo': 'La fecha de consumo no puede ser en el futuro.'
            })

    def save(self, *args, **kwargs):
        """
        Al guardar un consumo, descontar del stock del proyecto
        """
        self.full_clean()  # Ejecutar validaciones

        with transaction.atomic():
            # Verificar si hay suficiente stock en el proyecto
            try:
                pm = ProyectoMaterial.objects.select_for_update().get(
                    proyecto=self.proyecto,
                    material=self.material
                )

                if self.pk:  # Si es actualización
                    old = ConsumoMaterial.objects.get(pk=self.pk)
                    diferencia = self.cantidad_consumida - old.cantidad_consumida
                else:  # Si es nuevo
                    diferencia = self.cantidad_consumida

                # Verificar que hay suficiente stock (con tolerancia para redondeo)
                from decimal import Decimal
                tolerancia = Decimal('0.001')  # Tolerancia de 0.001 para errores de redondeo

                if diferencia > pm.stock_proyecto + tolerancia:
                    from django.core.exceptions import ValidationError
                    raise ValidationError(
                        f"Stock insuficiente. Disponible: {pm.stock_proyecto} {self.material.unit.symbol}"
                    )

                # Guardar el consumo
                super().save(*args, **kwargs)

                # Descontar del stock del proyecto
                pm.stock_proyecto = F("stock_proyecto") - diferencia
                pm.save()
                pm.refresh_from_db()

            except ProyectoMaterial.DoesNotExist:
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f"El material {self.material.name} no tiene stock asignado a este proyecto."
                )

    def delete(self, *args, **kwargs):
        """
        Al eliminar un consumo, restaurar el stock del proyecto
        """
        with transaction.atomic():
            try:
                # Obtener la relación ProyectoMaterial para restaurar el stock
                pm = ProyectoMaterial.objects.select_for_update().get(
                    proyecto=self.proyecto,
                    material=self.material
                )

                # Restaurar el stock del proyecto
                pm.stock_proyecto = F("stock_proyecto") + self.cantidad_consumida
                pm.save()
                pm.refresh_from_db()

                # Eliminar el consumo
                super().delete(*args, **kwargs)

            except ProyectoMaterial.DoesNotExist:
                # Si no existe la relación, solo eliminar el consumo
                super().delete(*args, **kwargs)


# SISTEMA DE PRESUPUESTO DETALLADO

class BudgetSection(models.Model):
    """
    Secciones del presupuesto detallado (23 secciones)
    """
    name = models.CharField(max_length=200, verbose_name="Nombre de la sección")
    order = models.PositiveIntegerField(verbose_name="Orden", default=0)
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_percentage = models.BooleanField(default=False, verbose_name="Es porcentual")
    percentage_value = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="Valor porcentual",
        help_text="Para secciones como Administración (12%)"
    )
    
    class Meta:
        verbose_name = "Sección de Presupuesto"
        verbose_name_plural = "Secciones de Presupuesto"
        ordering = ['order']
    
    def __str__(self):
        return f"{self.order}. {self.name}"


class BudgetItem(models.Model):
    """
    Ítems individuales dentro de cada sección del presupuesto
    """
    section = models.ForeignKey(
        BudgetSection, 
        on_delete=models.CASCADE, 
        related_name="items",
        verbose_name="Sección"
    )
    code = models.CharField(max_length=20, verbose_name="Código", blank=True)
    description = models.TextField(verbose_name="Descripción del ítem")
    unit = models.CharField(max_length=20, verbose_name="Unidad")
    unit_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        verbose_name="Precio Unitario (COP)",
        validators=[MinValueValidator(0)]
    )
    order = models.PositiveIntegerField(verbose_name="Orden en sección", default=0)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Ítem de Presupuesto"
        verbose_name_plural = "Ítems de Presupuesto"
        ordering = ['section__order', 'order']
    
    def __str__(self):
        return f"{self.section.name} - {self.description[:50]}"


class ProjectBudgetItem(models.Model):
    """
    Ítems de presupuesto específicos para cada proyecto
    """
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name="budget_items",
        verbose_name="Proyecto"
    )
    budget_item = models.ForeignKey(
        BudgetItem, 
        on_delete=models.CASCADE,
        verbose_name="Ítem de Presupuesto"
    )
    quantity = models.DecimalField(
        max_digits=12, 
        decimal_places=3, 
        default=0,
        verbose_name="Cantidad",
        validators=[MinValueValidator(0)]
    )
    unit_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        verbose_name="Precio Unitario",
        validators=[MinValueValidator(0)]
    )
    total_price = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name="Precio Total",
        validators=[MinValueValidator(0)]
    )
    
    class Meta:
        verbose_name = "Ítem de Presupuesto del Proyecto"
        verbose_name_plural = "Ítems de Presupuesto del Proyecto"
        unique_together = ['project', 'budget_item']
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        
        # Asegurar que unit_price no sea None
        if self.unit_price is None:
            self.unit_price = self.budget_item.unit_price
        
        # Asegurar que quantity y unit_price sean Decimal
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if not isinstance(self.unit_price, Decimal):
            self.unit_price = Decimal(str(self.unit_price))
        
        # Calcular total_price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.project.name} - {self.budget_item.description[:30]}"
