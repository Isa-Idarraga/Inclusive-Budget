from django import forms
from .models import Project, Role, Worker, EntradaMaterial, ConsumoMaterial, BudgetSection, BudgetItem, ProjectBudgetItem
from catalog.models import Material, Supplier

class EntradaMaterialForm(forms.ModelForm):
    class Meta:
        model = EntradaMaterial
        fields = ["material", "cantidad", "lote", "proveedor", "fecha_ingreso"]

    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        label="Material"
    )

    proveedor = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        label="Proveedor"
    )

    fecha_ingreso = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-inclusive',
            'type': 'date'
        }),
        label="Fecha de ingreso"
    )


# Formulario para registrar consumo diario de materiales (RF17A)
# Formulario para registrar consumo diario de materiales (RF17A + RF17B)
class ConsumoMaterialForm(forms.ModelForm):
    """
    Formulario para registrar el consumo diario de materiales
    Incluye validaciones según criterios de aceptación de RF17A y RF17B
    """
    class Meta:
        model = ConsumoMaterial
        fields = [
            'material',
            'cantidad_consumida',
            'fecha_consumo',
            'etapa_presupuesto',  # ✅ NUEVO CAMPO RF17B
            'componente_actividad',
            'observaciones'
        ]
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'cantidad_consumida': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': 'Ej: 25.5',
                'required': True
            }),
            'fecha_consumo': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'etapa_presupuesto': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'componente_actividad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cimentación, Muros primer piso, Instalación eléctrica',
                'maxlength': '200',
                'required': True
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales (opcional)'
            }),
        }
        labels = {
            'material': 'Material *',
            'cantidad_consumida': 'Cantidad consumida *',
            'fecha_consumo': 'Fecha de consumo *',
            'etapa_presupuesto': 'Etapa del presupuesto *',
            'componente_actividad': 'Componente/Actividad *',
            'observaciones': 'Observaciones'
        }
        help_texts = {
            'cantidad_consumida': 'Cantidad del material que se consumió',
            'etapa_presupuesto': 'Seleccione la etapa/categoría del presupuesto a la que pertenece este consumo',
            'componente_actividad': 'Actividad o parte del proyecto donde se usó el material',
        }

    def __init__(self, *args, **kwargs):
        # Recibimos el proyecto desde la vista
        proyecto = kwargs.pop("proyecto", None)
        super().__init__(*args, **kwargs)

        # 🔹 Filtrar las etapas para mostrar SOLO las 23 secciones base globales
        self.fields["etapa_presupuesto"].queryset = (
            BudgetSection.objects.filter(project__isnull=True).order_by("order")
        )

        # 🔹 Mejorar la etiqueta visual del combo
        self.fields["etapa_presupuesto"].label_from_instance = (
            lambda obj: f"{obj.order}. {obj.name}"
        )

        # 🔹 Hacer obligatorio el campo
        self.fields["etapa_presupuesto"].required = True

        # Guardar el proyecto actual (opcional, por si lo usas luego)
        self._proyecto = proyecto
        
    def clean_cantidad_consumida(self):
        """Sin validaciones - permite cualquier valor"""
        return self.cleaned_data.get('cantidad_consumida')

    def clean_fecha_consumo(self):
        """Validar que la fecha no sea futura"""
        from django.utils import timezone
        fecha = self.cleaned_data.get('fecha_consumo')
        if fecha and fecha > timezone.now().date():
            raise forms.ValidationError('La fecha de consumo no puede ser en el futuro.')
        return fecha

    def clean_componente_actividad(self):
        """Validar que el componente/actividad no esté vacío"""
        componente = self.cleaned_data.get('componente_actividad', '').strip()
        if not componente:
            raise forms.ValidationError('Debe especificar el componente o actividad.')
        return componente

    def clean_etapa_presupuesto(self):
        """Validar que la etapa del presupuesto esté seleccionada (RF17B)"""
        etapa = self.cleaned_data.get('etapa_presupuesto')
        if not etapa:
            raise forms.ValidationError('Debe seleccionar la etapa del presupuesto.')
        return etapa

    def clean(self):
        """
        Validación completa del formulario (RF17D)
        Verifica que haya suficiente stock para el consumo
        """
        cleaned_data = super().clean()
        material = cleaned_data.get('material')
        cantidad_consumida = cleaned_data.get('cantidad_consumida')

        if material and cantidad_consumida and hasattr(self, 'proyecto'):
            from .models import ProyectoMaterial

            try:
                pm = ProyectoMaterial.objects.get(
                    proyecto=self.proyecto,
                    material=material
                )

                # Si estamos editando, restar la cantidad anterior
                cantidad_actual_a_consumir = cantidad_consumida
                if self.instance.pk:
                    cantidad_actual_a_consumir = cantidad_consumida - self.instance.cantidad_consumida

                # Verificar si hay suficiente stock
                if pm.stock_proyecto < cantidad_actual_a_consumir:
                    # Guardar el stock disponible para mostrarlo en el template
                    self.stock_disponible = pm.stock_proyecto
                    self.material_nombre = material.name
                    self.material_unidad = material.unit.symbol

                    raise forms.ValidationError(
                        f'Stock insuficiente para este consumo. '
                        f'Disponible: {pm.stock_proyecto} {material.unit.symbol}. '
                        f'Solicitado: {cantidad_actual_a_consumir} {material.unit.symbol}.'
                    )

            except ProyectoMaterial.DoesNotExist:
                raise forms.ValidationError(
                    f'El material {material.name} no tiene stock asignado a este proyecto. '
                    f'Debe registrar una entrada de material primero.'
                )

        return cleaned_data


# Formulario para Role
class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name", "description", "salario_base_dia"]


# Formulario para Worker
class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["name", "phone", "cedula", "direccion", "role"]


class ProjectForm(forms.ModelForm):
    """
    Formulario para crear y editar proyectos
    """

    class Meta:
        model = Project
        fields = [
            # Información básica
            "name",
            "location_address",
            "description",
            "estado",
            "imagen_proyecto",
            # 1. Datos generales del proyecto
            "ubicacion_proyecto",
            "otra_ubicacion",
            "area_construida_total",
            "numero_pisos",
            "area_exterior_intervenir",
            # 2. Terreno y preliminares
            "tipo_terreno",
            "acceso_obra",
            "requiere_cerramiento",
            # 3. Estructura y cimentación
            "sistema_entrepiso",
            "exigencia_estructural",
            # 4. Muros y acabados básicos
            "relacion_muros",
            "acabado_muros",
            "cielorrasos",
            # 5. Pisos y enchapes
            "piso_zona_social",
            "piso_habitaciones",
            "numero_banos",
            "nivel_enchape_banos",
            # 6. Carpinterías
            "puertas_interiores",
            "puerta_principal_especial",
            "porcentaje_ventanas",
            "metros_mueble_cocina",
            "vestier_closets",
            # 7. Hidrosanitario
            "calentador_gas",
            "incluye_lavadero",
            "punto_lavaplatos",
            "punto_lavadora",
            "punto_lavadero",
            # 8. Instalaciones eléctricas y gas
            "dotacion_electrica",
            "red_gas_natural",
            # 9. Cubierta e impermeabilización
            "tipo_cubierta",
            "impermeabilizacion_adicional",
            # 10. Exteriores y paisajismo
            "area_adoquin",
            "area_zonas_verdes",
            # 11. Indirectos y profesionales
            "incluir_estudios_disenos",
            "incluir_licencia_impuestos",
            # Campos heredados (compatibilidad) - Excluir doors_height temporalmente
            "built_area",
            "exterior_area",
            "columns_count",
            "walls_area",
            "windows_area",
            "doors_count",
        ]

        widgets = {
            # Información básica
            "name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "Ej: Casa Familiar Los Pinos",
                }
            ),
            "location_address": forms.TextInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "Ej: Calle 123 #45-67, Medellín",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "rows": 3,
                    "placeholder": "Describa las características principales del proyecto...",
                }
            ),
            "estado": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "imagen_proyecto": forms.FileInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "accept": "image/*",
                }
            ),
            # 1. Datos generales del proyecto
            "ubicacion_proyecto": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "otra_ubicacion": forms.TextInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "Especifique la ciudad",
                }
            ),
            "area_construida_total": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "120",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "numero_pisos": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "area_exterior_intervenir": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "50",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            # 2. Terreno y preliminares
            "tipo_terreno": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "acceso_obra": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "requiere_cerramiento": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            # 3. Estructura y cimentación
            "sistema_entrepiso": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "exigencia_estructural": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            # 4. Muros y acabados básicos
            "relacion_muros": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "acabado_muros": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "cielorrasos": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            # 5. Pisos y enchapes
            "piso_zona_social": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "piso_habitaciones": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "numero_banos": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "2",
                    "min": "0",
                }
            ),
            "nivel_enchape_banos": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            # 6. Carpinterías
            "puertas_interiores": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "8",
                    "min": "0",
                }
            ),
            "puerta_principal_especial": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "porcentaje_ventanas": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "metros_mueble_cocina": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "3",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "vestier_closets": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            # 7. Hidrosanitario
            "calentador_gas": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "incluye_lavadero": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "punto_lavaplatos": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "punto_lavadora": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "punto_lavadero": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # 8. Instalaciones eléctricas y gas
            "dotacion_electrica": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "red_gas_natural": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # 9. Cubierta e impermeabilización
            "tipo_cubierta": forms.Select(
                attrs={"class": "form-control form-control-inclusive"}
            ),
            "impermeabilizacion_adicional": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            # 10. Exteriores y paisajismo
            "area_adoquin": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "40",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "area_zonas_verdes": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "30",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            # 11. Indirectos y profesionales
            "incluir_estudios_disenos": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "incluir_licencia_impuestos": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            # Campos heredados (compatibilidad)
            "built_area": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "120.50",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "exterior_area": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "80.25",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "columns_count": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "8",
                    "min": "0",
                }
            ),
            "walls_area": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "200.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "windows_area": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "15.75",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "doors_count": forms.NumberInput(
                attrs={
                    "class": "form-control form-control-inclusive",
                    "placeholder": "6",
                    "min": "0",
                }
            ),
        }

        labels = {
            # Información básica
            "name": "Nombre del proyecto",
            "location_address": "Dirección ubicación",
            "description": "Descripción del proyecto",
            "estado": "Estado del proyecto",
            "imagen_proyecto": "Imagen del proyecto",
            # 1. Datos generales del proyecto
            "ubicacion_proyecto": "Ubicación del proyecto",
            "otra_ubicacion": "Otra ubicación (especificar)",
            "area_construida_total": "Área construida total (m²)",
            "numero_pisos": "Número de pisos",
            "area_exterior_intervenir": "Área exterior a intervenir (m²)",
            # 2. Terreno y preliminares
            "tipo_terreno": "Tipo de terreno predominante",
            "acceso_obra": "Acceso a la obra",
            "requiere_cerramiento": "¿Requiere cerramiento provisional?",
            # 3. Estructura y cimentación
            "sistema_entrepiso": "Sistema de entrepiso / losa",
            "exigencia_estructural": "Nivel de exigencia estructural",
            # 4. Muros y acabados básicos
            "relacion_muros": "Relación muros / área construida",
            "acabado_muros": "Acabado de muros interiores",
            "cielorrasos": "Cielorrasos",
            # 5. Pisos y enchapes
            "piso_zona_social": "Tipo de piso en zona social",
            "piso_habitaciones": "Tipo de piso en habitaciones",
            "numero_banos": "Número de baños completos",
            "nivel_enchape_banos": "Nivel de enchape en baños",
            # 6. Carpinterías
            "puertas_interiores": "Cantidad de puertas interiores",
            "puerta_principal_especial": "¿Puerta principal especial (seguridad o madera maciza)?",
            "porcentaje_ventanas": "Porcentaje aproximado de fachada en ventanas",
            "metros_mueble_cocina": "Cocina – metros lineales de mueble bajo",
            "vestier_closets": "Vestier o closets",
            # 7. Hidrosanitario
            "calentador_gas": "¿Tendrá calentador de agua a gas?",
            "incluye_lavadero": "¿Incluye lavadero / zona de ropas?",
            "punto_lavaplatos": "Punto lavaplatos",
            "punto_lavadora": "Punto lavadora",
            "punto_lavadero": "Punto lavadero",
            # 8. Instalaciones eléctricas y gas
            "dotacion_electrica": "Nivel de dotación eléctrica",
            "red_gas_natural": "¿Incluye red de gas natural?",
            # 9. Cubierta e impermeabilización
            "tipo_cubierta": "Tipo de cubierta",
            "impermeabilizacion_adicional": "¿Requiere impermeabilización adicional en terrazas o duchas?",
            # 10. Exteriores y paisajismo
            "area_adoquin": "Área aproximada de adoquín exterior (m²)",
            "area_zonas_verdes": "Área aproximada de zonas verdes (m²)",
            # 11. Indirectos y profesionales
            "incluir_estudios_disenos": "¿Incluir costos de estudios y diseños (arquitectónico, estructural, eléctrico, hidráulico)?",
            "incluir_licencia_impuestos": "¿Incluir costos de licencia e impuestos de construcción?",
            # Campos heredados (compatibilidad)
            "built_area": "Metros² de construido (casa) - Campo heredado",
            "exterior_area": "Metros² de exteriores - Campo heredado",
            "columns_count": "Número de columnas - Campo heredado",
            "walls_area": "Metros² de paredes - Campo heredado",
            "windows_area": "Metros² de ventanas - Campo heredado",
            "doors_count": "Número de puertas - Campo heredado",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hacer que el campo otra_ubicacion sea condicional
        self.fields["otra_ubicacion"].required = False

        # Configurar campos como no requeridos por defecto
        optional_fields = [
            "description",
            "imagen_proyecto",
            "otra_ubicacion",
            "built_area",
            "exterior_area",
            "columns_count",
            "walls_area",
            "windows_area",
            "doors_count",
            # Hacer opcionales la mayoría de campos del cuestionario detallado
            "area_exterior_intervenir",
            "metros_mueble_cocina",
            "area_adoquin",
            "area_zonas_verdes",
        ]

        # Solo requerir campos básicos esenciales
        required_fields = [
            "name",
            "location_address",
            "ubicacion_proyecto",
            "area_construida_total",
            "numero_pisos",
        ]

        # Asegurar que doors_height no sea requerido
        if "doors_height" in self.fields:
            self.fields["doors_height"].required = False

        # Hacer todos los campos opcionales excepto los esenciales
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False

    def clean(self):
        cleaned_data = super().clean()

        # Validar que si selecciona "otra" ubicación, especifique cuál
        ubicacion = cleaned_data.get("ubicacion_proyecto")
        otra_ubicacion = cleaned_data.get("otra_ubicacion")

        if ubicacion == "otra" and not otra_ubicacion:
            raise forms.ValidationError(
                {"otra_ubicacion": 'Debe especificar la ubicación si selecciona "Otra"'}
            )

        # Asegurar valores por defecto para campos heredados (compatibilidad)
        if not cleaned_data.get("built_area"):
            cleaned_data["built_area"] = cleaned_data.get("area_construida_total") or 0

        if not cleaned_data.get("exterior_area"):
            cleaned_data["exterior_area"] = (
                cleaned_data.get("area_exterior_intervenir") or 0
            )

        if not cleaned_data.get("columns_count"):
            cleaned_data["columns_count"] = 0

        if not cleaned_data.get("walls_area"):
            cleaned_data["walls_area"] = 0

        if not cleaned_data.get("windows_area"):
            cleaned_data["windows_area"] = 0

        if not cleaned_data.get("doors_count"):
            cleaned_data["doors_count"] = 0

        # Simplificar manejo de campos decimales
        # No asignar doors_height aquí, se manejará en la vista

        return cleaned_data


# FORMULARIOS PARA PRESUPUESTO DETALLADO

class DetailedProjectForm(forms.ModelForm):
    """
    Formulario para crear proyectos con presupuesto detallado
    Solo para JEFE y CONSTRUCTOR
    """
    administration_percentage = forms.DecimalField(
        label="Porcentaje de Administración",
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=False,
        help_text="Porcentaje sobre el costo directo (0-100%)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '100'
        })
    )
    
    class Meta:
        model = Project
        fields = [
            # Información básica
            "name",
            "location_address", 
            "description",
            "estado",
            "imagen_proyecto",
            "administration_percentage",
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el nombre del proyecto'
            }),
            'location_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa la dirección del proyecto',
                'rows': 3
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe brevemente el proyecto',
                'rows': 4
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'imagen_proyecto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer campos requeridos
        self.fields["name"].required = True
        self.fields["location_address"].required = True
        
        # Hacer campos opcionales
        self.fields["description"].required = False
        self.fields["imagen_proyecto"].required = False


class BudgetItemForm(forms.ModelForm):
    """
    Formulario para editar un ítem del presupuesto
    """
    class Meta:
        model = ProjectBudgetItem
        fields = ["quantity", "unit_price"]
        widgets = {
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.001",
                "min": "0"
            }),
            "unit_price": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity"].label = "Cantidad"
        self.fields["unit_price"].label = "Precio Unitario (COP)"
    
    def clean_quantity(self):
        """Sin validaciones - permite cualquier valor"""
        return self.cleaned_data.get("quantity")
    
    def clean_unit_price(self):
        """Sin validaciones - permite cualquier valor"""
        return self.cleaned_data.get("unit_price")


class BudgetSectionForm(forms.Form):
    """
    Formulario para manejar una sección completa del presupuesto
    """
    def __init__(self, section, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = section
        self.project = project
        
        # Obtener ítems de la sección
        items = BudgetItem.objects.filter(section=section, is_active=True).order_by('order')
        
        for item in items:
            # Para proyectos existentes, obtener datos guardados
            if project and project.pk:
                try:
                    project_item = ProjectBudgetItem.objects.get(
                        project=project,
                        budget_item=item
                    )
                    initial_quantity = project_item.quantity
                    initial_price = project_item.unit_price
                except ProjectBudgetItem.DoesNotExist:
                    initial_quantity = 0
                    initial_price = item.unit_price
            else:
                # Para proyectos nuevos, usar valores por defecto
                initial_quantity = 0
                initial_price = item.unit_price
            
            # Crear solo campos de cantidad (los precios son fijos)
            self.fields[f'quantity_{item.id}'] = forms.DecimalField(
                initial=initial_quantity,
                max_digits=12,
                decimal_places=3,
                min_value=0,
                required=False,
                widget=forms.NumberInput(attrs={
                    "class": "form-control quantity-input",
                    "step": "0.001",
                    "min": "0",
                    "data-item-id": item.id
                })
            )
    
    def save(self, project):
        """Guardar los datos del formulario en el proyecto"""
        if not project:
            return
            
        items_saved = 0
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('quantity_'):
                item_id = field_name.replace('quantity_', '')
                try:
                    item = BudgetItem.objects.get(id=item_id)
                    # Para el formulario de creación, usar el precio del ítem por defecto
                    # Los precios se envían como campos hidden, no editables
                    unit_price = item.unit_price
                    
                    # Crear/actualizar siempre, incluso con cantidad 0
                    quantity_value = value if value is not None else 0
                    
                    project_item, created = ProjectBudgetItem.objects.get_or_create(
                        project=project,
                        budget_item=item,
                        defaults={
                            'quantity': quantity_value,
                            'unit_price': unit_price
                        }
                    )
                    
                    if not created:
                        project_item.quantity = quantity_value
                        project_item.unit_price = unit_price
                        project_item.save()
                    
                    items_saved += 1
                    print(f"DEBUG: Guardado {item.code} - Cantidad: {quantity_value} - Precio: ${unit_price}")
                        
                except BudgetItem.DoesNotExist:
                    continue
        
        print(f"DEBUG: Total ítems guardados en sección {self.section.name}: {items_saved}")


class BudgetManagementForm(forms.ModelForm):
    """
    Formulario para gestionar precios unitarios (solo JEFE)
    """
    class Meta:
        model = BudgetItem
        fields = ["unit_price", "is_active"]
        widgets = {
            "unit_price": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Precio en COP (sin decimales)"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_price"].label = "Precio Unitario (COP)"
        self.fields["is_active"].label = "Activo"
        
        # Formatear el precio sin decimales
        if self.instance and self.instance.pk:
            self.fields["unit_price"].initial = int(self.instance.unit_price)
    
    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price:
            # Convertir a entero si es posible
            try:
                # Remover cualquier formato de miles
                clean_value = str(unit_price).replace(',', '').replace('.', '')
                return int(clean_value)
            except (ValueError, TypeError):
                raise forms.ValidationError("Por favor ingresa un precio válido (solo números enteros)")
        return unit_price


class BudgetItemCreateForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ["section", "code", "description", "unit", "unit_price", "is_active"]
        widgets = {
            "section": forms.Select(attrs={
                "class": "form-select"
            }),
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 1.1, 2.3, etc."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descripción detallada del ítem"
            }),
            "unit": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: m², gl, und, etc."
            }),
            "unit_price": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Precio en COP (ej: 1500000)"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section"].label = "Sección"
        self.fields["code"].label = "Código"
        self.fields["description"].label = "Descripción"
        self.fields["unit"].label = "Unidad"
        self.fields["unit_price"].label = "Precio Unitario (COP)"
        self.fields["is_active"].label = "Activo"
        
        # Ordenar secciones por número
        self.fields["section"].queryset = BudgetSection.objects.all().order_by('order')


class BudgetItemEditForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ["code", "description", "unit", "unit_price", "is_active"]
        widgets = {
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 1.1, 2.3, etc."
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Descripción detallada del ítem"
            }),
            "unit": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: m², gl, und, etc."
            }),
            "unit_price": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Precio en COP (ej: 1500000)",
                "type": "text"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["code"].label = "Código"
        self.fields["description"].label = "Descripción"
        self.fields["unit"].label = "Unidad"
        self.fields["unit_price"].label = "Precio Unitario (COP)"
        self.fields["is_active"].label = "Activo"
        
        # Formatear el precio sin decimales si existe
        if self.instance and self.instance.unit_price:
            self.initial['unit_price'] = str(int(self.instance.unit_price))
    
    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        if unit_price:
            # Limpiar el valor de comas y puntos
            clean_value = str(unit_price).replace(',', '').replace('.', '')
            try:
                return int(clean_value)
            except (ValueError, TypeError):
                raise forms.ValidationError("Por favor ingresa un precio válido (solo números enteros)")
        return unit_price
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Si no tiene order, asignar el siguiente número en la sección
        if not instance.order:
            from django.db.models import Max
            last_order = BudgetItem.objects.filter(section=instance.section).aggregate(
                max_order=Max('order')
            )['max_order'] or 0
            instance.order = last_order + 1
        if commit:
            instance.save()
        return instance
