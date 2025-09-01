from django import forms
from .models import Project

class ProjectForm(forms.ModelForm):
    """
    Formulario expandido para crear y editar proyectos
    Incluye cuestionario detallado para cálculo preciso de presupuestos
    """
    
    class Meta:
        model = Project
        fields = [
            # Información básica
            'name', 'location_address', 'description', 'estado', 'imagen_proyecto',
            
            # 1. Datos generales del proyecto
            'ubicacion_proyecto', 'otra_ubicacion', 'area_construida_total', 'numero_pisos', 'area_exterior_intervenir',
            
            # 2. Terreno y preliminares
            'tipo_terreno', 'acceso_obra', 'requiere_cerramiento',
            
            # 3. Estructura y cimentación
            'sistema_entrepiso', 'exigencia_estructural',
            
            # 4. Muros y acabados básicos
            'relacion_muros', 'acabado_muros', 'cielorrasos',
            
            # 5. Pisos y enchapes
            'piso_zona_social', 'piso_habitaciones', 'numero_banos', 'nivel_enchape_banos',
            
            # 6. Carpinterías
            'puertas_interiores', 'puerta_principal_especial', 'porcentaje_ventanas', 'metros_mueble_cocina', 'vestier_closets',
            
            # 7. Hidrosanitario
            'calentador_gas', 'incluye_lavadero', 'punto_lavaplatos', 'punto_lavadora', 'punto_lavadero',
            
            # 8. Instalaciones eléctricas y gas
            'dotacion_electrica', 'red_gas_natural',
            
            # 9. Cubierta e impermeabilización
            'tipo_cubierta', 'impermeabilizacion_adicional',
            
            # 10. Exteriores y paisajismo
            'area_adoquin', 'area_zonas_verdes',
            
            # 11. Indirectos y profesionales
            'incluir_estudios_disenos', 'incluir_licencia_impuestos',
            
            # Campos heredados (compatibilidad) - Excluir doors_height temporalmente
            'built_area', 'exterior_area', 'columns_count', 'walls_area', 'windows_area', 'doors_count'
        ]
        
        widgets = {
            # Información básica
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': 'Ej: Casa Familiar Los Pinos'
            }),
            'location_address': forms.TextInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': 'Ej: Calle 123 #45-67, Medellín'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-inclusive',
                'rows': 3,
                'placeholder': 'Describa las características principales del proyecto...'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'imagen_proyecto': forms.FileInput(attrs={
                'class': 'form-control form-control-inclusive',
                'accept': 'image/*'
            }),
            
            # 1. Datos generales del proyecto
            'ubicacion_proyecto': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'otra_ubicacion': forms.TextInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': 'Especifique la ciudad'
            }),
            'area_construida_total': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '120',
                'step': '0.01',
                'min': '0'
            }),
            'numero_pisos': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'area_exterior_intervenir': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '50',
                'step': '0.01',
                'min': '0'
            }),
            
            # 2. Terreno y preliminares
            'tipo_terreno': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'acceso_obra': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'requiere_cerramiento': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # 3. Estructura y cimentación
            'sistema_entrepiso': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'exigencia_estructural': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            
            # 4. Muros y acabados básicos
            'relacion_muros': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'acabado_muros': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'cielorrasos': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            
            # 5. Pisos y enchapes
            'piso_zona_social': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'piso_habitaciones': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'numero_banos': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '2',
                'min': '0'
            }),
            'nivel_enchape_banos': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            
            # 6. Carpinterías
            'puertas_interiores': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '8',
                'min': '0'
            }),
            'puerta_principal_especial': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'porcentaje_ventanas': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'metros_mueble_cocina': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '3',
                'step': '0.01',
                'min': '0'
            }),
            'vestier_closets': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            
            # 7. Hidrosanitario
            'calentador_gas': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'incluye_lavadero': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'punto_lavaplatos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'punto_lavadora': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'punto_lavadero': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # 8. Instalaciones eléctricas y gas
            'dotacion_electrica': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'red_gas_natural': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # 9. Cubierta e impermeabilización
            'tipo_cubierta': forms.Select(attrs={
                'class': 'form-control form-control-inclusive'
            }),
            'impermeabilizacion_adicional': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # 10. Exteriores y paisajismo
            'area_adoquin': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '40',
                'step': '0.01',
                'min': '0'
            }),
            'area_zonas_verdes': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '30',
                'step': '0.01',
                'min': '0'
            }),
            
            # 11. Indirectos y profesionales
            'incluir_estudios_disenos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'incluir_licencia_impuestos': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # Campos heredados (compatibilidad)
            'built_area': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '120.50',
                'step': '0.01',
                'min': '0'
            }),
            'exterior_area': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '80.25',
                'step': '0.01',
                'min': '0'
            }),
            'columns_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '8',
                'min': '0'
            }),
            'walls_area': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '200.00',
                'step': '0.01',
                'min': '0'
            }),
            'windows_area': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '15.75',
                'step': '0.01',
                'min': '0'
            }),
            'doors_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-inclusive',
                'placeholder': '6',
                'min': '0'
            }),
        }
        
        labels = {
            # Información básica
            'name': 'Nombre del proyecto',
            'location_address': 'Dirección ubicación',
            'description': 'Descripción del proyecto',
            'estado': 'Estado del proyecto',
            'imagen_proyecto': 'Imagen del proyecto',
            
            # 1. Datos generales del proyecto
            'ubicacion_proyecto': 'Ubicación del proyecto',
            'otra_ubicacion': 'Otra ubicación (especificar)',
            'area_construida_total': 'Área construida total (m²)',
            'numero_pisos': 'Número de pisos',
            'area_exterior_intervenir': 'Área exterior a intervenir (m²)',
            
            # 2. Terreno y preliminares
            'tipo_terreno': 'Tipo de terreno predominante',
            'acceso_obra': 'Acceso a la obra',
            'requiere_cerramiento': '¿Requiere cerramiento provisional?',
            
            # 3. Estructura y cimentación
            'sistema_entrepiso': 'Sistema de entrepiso / losa',
            'exigencia_estructural': 'Nivel de exigencia estructural',
            
            # 4. Muros y acabados básicos
            'relacion_muros': 'Relación muros / área construida',
            'acabado_muros': 'Acabado de muros interiores',
            'cielorrasos': 'Cielorrasos',
            
            # 5. Pisos y enchapes
            'piso_zona_social': 'Tipo de piso en zona social',
            'piso_habitaciones': 'Tipo de piso en habitaciones',
            'numero_banos': 'Número de baños completos',
            'nivel_enchape_banos': 'Nivel de enchape en baños',
            
            # 6. Carpinterías
            'puertas_interiores': 'Cantidad de puertas interiores',
            'puerta_principal_especial': '¿Puerta principal especial (seguridad o madera maciza)?',
            'porcentaje_ventanas': 'Porcentaje aproximado de fachada en ventanas',
            'metros_mueble_cocina': 'Cocina – metros lineales de mueble bajo',
            'vestier_closets': 'Vestier o closets',
            
            # 7. Hidrosanitario
            'calentador_gas': '¿Tendrá calentador de agua a gas?',
            'incluye_lavadero': '¿Incluye lavadero / zona de ropas?',
            'punto_lavaplatos': 'Punto lavaplatos',
            'punto_lavadora': 'Punto lavadora',
            'punto_lavadero': 'Punto lavadero',
            
            # 8. Instalaciones eléctricas y gas
            'dotacion_electrica': 'Nivel de dotación eléctrica',
            'red_gas_natural': '¿Incluye red de gas natural?',
            
            # 9. Cubierta e impermeabilización
            'tipo_cubierta': 'Tipo de cubierta',
            'impermeabilizacion_adicional': '¿Requiere impermeabilización adicional en terrazas o duchas?',
            
            # 10. Exteriores y paisajismo
            'area_adoquin': 'Área aproximada de adoquín exterior (m²)',
            'area_zonas_verdes': 'Área aproximada de zonas verdes (m²)',
            
            # 11. Indirectos y profesionales
            'incluir_estudios_disenos': '¿Incluir costos de estudios y diseños (arquitectónico, estructural, eléctrico, hidráulico)?',
            'incluir_licencia_impuestos': '¿Incluir costos de licencia e impuestos de construcción?',
            
            # Campos heredados (compatibilidad)
            'built_area': 'Metros² de construido (casa) - Campo heredado',
            'exterior_area': 'Metros² de exteriores - Campo heredado',
            'columns_count': 'Número de columnas - Campo heredado',
            'walls_area': 'Metros² de paredes - Campo heredado',
            'windows_area': 'Metros² de ventanas - Campo heredado',
            'doors_count': 'Número de puertas - Campo heredado',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer que el campo otra_ubicacion sea condicional
        self.fields['otra_ubicacion'].required = False
        
        # Configurar campos como no requeridos por defecto
        optional_fields = [
            'description', 'imagen_proyecto', 'otra_ubicacion',
            'built_area', 'exterior_area', 'columns_count', 'walls_area', 
            'windows_area', 'doors_count',
            # Hacer opcionales la mayoría de campos del cuestionario detallado
            'area_exterior_intervenir', 'metros_mueble_cocina', 'area_adoquin', 'area_zonas_verdes'
        ]
        
        # Solo requerir campos básicos esenciales
        required_fields = ['name', 'location_address', 'ubicacion_proyecto', 'area_construida_total', 'numero_pisos']
        
        # Asegurar que doors_height no sea requerido
        if 'doors_height' in self.fields:
            self.fields['doors_height'].required = False
        
        # Hacer todos los campos opcionales excepto los esenciales
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validar que si selecciona "otra" ubicación, especifique cuál
        ubicacion = cleaned_data.get('ubicacion_proyecto')
        otra_ubicacion = cleaned_data.get('otra_ubicacion')
        
        if ubicacion == 'otra' and not otra_ubicacion:
            raise forms.ValidationError({
                'otra_ubicacion': 'Debe especificar la ubicación si selecciona "Otra"'
            })
        
        # Asegurar valores por defecto para campos heredados (compatibilidad)
        if not cleaned_data.get('built_area'):
            cleaned_data['built_area'] = cleaned_data.get('area_construida_total') or 0
        
        if not cleaned_data.get('exterior_area'):
            cleaned_data['exterior_area'] = cleaned_data.get('area_exterior_intervenir') or 0
            
        if not cleaned_data.get('columns_count'):
            cleaned_data['columns_count'] = 0
            
        if not cleaned_data.get('walls_area'):
            cleaned_data['walls_area'] = 0
            
        if not cleaned_data.get('windows_area'):
            cleaned_data['windows_area'] = 0
            
        if not cleaned_data.get('doors_count'):
            cleaned_data['doors_count'] = 0
            
        # Simplificar manejo de campos decimales
        # No asignar doors_height aquí, se manejará en la vista
        
        return cleaned_data