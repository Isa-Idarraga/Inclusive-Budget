# chatbot/flow_handlers.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from .models import Conversation, ConversationState
from .utils.chat_utils import generar_pregunta
from .utils.input_parser import interpretar_respuesta


def convert_decimals(obj):
    """Recursively convert Decimal objects to float in nested structures"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


def get_field_example(field_name, field):
    """Genera ejemplos contextuales para los campos del formulario"""
    examples = {
        'name': 'Casa Familiar López, Edificio Centro Empresarial',
        'title': 'Construcción Casa Campestre, Remodelación Oficinas',
        'description': 'Construcción de vivienda unifamiliar de 2 pisos con acabados en ladrillo',
        'location': 'Cra 45 #23-10, Medellín; Vereda La Estrella, Envigado',
        'location_address': 'Calle 50 #30-20, Barrio Laureles',
        'city': 'Medellín, Bogotá, Cali',
        'address': 'Calle 50 #30-20, Barrio Laureles',
        'ubicacion_proyecto': 'Medellín, Bogotá, Otra ciudad',
        'otra_ubicacion': 'Envigado, Sabaneta, Itagüí',
        'area': '120, 85.5, 200 (en metros cuadrados)',
        'terrain_area': '150, 180.5, 250 (área del terreno en m²)',
        'construction_area': '120, 95, 180 (área a construir en m²)',
        'area_construida_total': '120, 85.5, 200 (en metros cuadrados)',
        'area_exterior_intervenir': '30, 50, 75 (área exterior en m²)',
        'built_area': '120, 95, 180 (área construida en m²)',
        'exterior_area': '30, 45, 60 (área exterior en m²)',
        'walls_area': '80, 120, 150 (área de muros en m²)',
        'windows_area': '15, 20, 30 (área de ventanas en m²)',
        'floors': '1, 2, 3 (número de pisos)',
        'numero_pisos': '1, 2, 3_mas',
        'rooms': '3, 2, 4 (número de habitaciones)',
        'bathrooms': '2, 1, 3 (número de baños completos)',
        'numero_banos': '1, 2, 3 (número de baños)',
        'parking': '1, 2, 0 (espacios de parqueadero)',
        'columns_count': '4, 8, 12 (número de columnas)',
        'doors_count': '5, 7, 10 (número de puertas)',
        'puertas_interiores': '3, 5, 7 (puertas interiores)',
        'doors_height': '2.1, 2.2, 2.4 (altura de puertas en metros)',
        'metros_mueble_cocina': '3, 6, 9 (metros lineales de cocina)',
        'start_date': '2025-12-01, 01/12/2025',
        'end_date': '2026-06-30, 30/06/2026',
        'estimated_start': '15/01/2026',
        'estimated_end': '15/12/2026',
        'budget': '150000000, 80000000 (en pesos colombianos)',
        'estimated_cost': '120000000, 95500000',
        'price': '2500000, 1800000',
        'presupuesto': '100000000, 150000000',
        'tipo_terreno': 'normal, dificil, facil',
        'acceso_obra': 'facil, medio, dificil',
        'sistema_entrepiso': 'maciza, aligerada',
        'exigencia_estructural': 'normal, alta',
        'relacion_muros': 'baja, media, alta',
        'acabado_muros': 'basico, estandar, premium',
        'cielorrasos': 'ninguno, parcial, total',
        'finish_type': 'básico, estándar, premium, lujo',
        'finish_level': 'básico, medio, alto',
        'piso_zona_social': 'ceramica, porcelanato, madera',
        'piso_habitaciones': 'ceramica, porcelanato, madera',
        'nivel_enchape_banos': 'bajo, medio, alto',
        'construction_type': 'casa, apartamento, local comercial, bodega',
        'puerta_principal_especial': 'sí, no',
        'porcentaje_ventanas': 'bajo, medio, alto',
        'vestier_closets': 'ninguno, basico, medio, completo',
        'has_garage': 'sí, no, con garaje para 2 carros',
        'has_garden': 'sí, no, zona verde pequeña',
        'includes_kitchen': 'sí con cocina integral, no, cocina básica',
        'includes_closets': 'sí en todas las habitaciones, no, solo 2',
        'requiere_cerramiento': 'sí, no',
        'calentador_gas': 'sí, no',
        'incluye_lavadero': 'sí, no',
        'punto_lavaplatos': 'sí, no',
        'punto_lavadora': 'sí, no',
        'punto_lavadero': 'sí, no',
        'red_gas_natural': 'sí, no',
        'impermeabilizacion_adicional': 'sí, no',
        'incluir_estudios_disenos': 'sí, no',
        'incluir_licencia_impuestos': 'sí, no',
        'dotacion_electrica': 'basica, estandar, completa',
        'tipo_cubierta': 'tradicional, teja, concreto',
        'area_adoquin': '0, 20, 40 (área de adoquín en m²)',
        'area_zonas_verdes': '0, 30, 60 (área de zonas verdes en m²)',
        'client_name': 'Juan Pérez, María González López',
        'client_email': 'juan.perez@email.com',
        'client_phone': '3001234567, 300-123-4567',
        'contact': 'Carlos Ruiz - 3101234567',
        'status': 'planificación, en progreso, pausado, completado',
        'estado': 'futuro, activo, pausado, finalizado',
        'priority': 'alta, media, baja',
        'notes': 'El cliente prefiere materiales ecológicos y acabados modernos',
        'observations': 'Considerar restricciones de POT para altura de construcción',
        'comments': 'Solicitar permisos de construcción con antelación',
    }
    
    if field_name in examples:
        return examples[field_name]
    
    field_lower = field_name.lower()
    for key, example in examples.items():
        if key in field_lower or field_lower in key:
            return examples[key]
    
    field_class = field.__class__.__name__
    if 'Integer' in field_class or 'Decimal' in field_class or 'Float' in field_class:
        return '100, 50.5, 1500'
    elif 'Date' in field_class:
        return '2025-12-01, 01/12/2025'
    elif 'Email' in field_class:
        return 'correo@ejemplo.com'
    elif 'Boolean' in field_class:
        return 'sí, no'
    elif 'Choice' in field_class:
        choices = getattr(field, 'choices', [])
        if choices:
            choice_examples = ', '.join([str(c[0]) for c in choices[:3]])
            return f'{choice_examples}'
    
    return 'Ingresa tu respuesta aquí'


class BaseFlowHandler(ABC):
    """Clase base para manejar flujos de conversación"""
    
    def __init__(self, conversation: Conversation):
        self.conversation = conversation
    
    @abstractmethod
    def start(self) -> str:
        """Inicia el flujo y retorna el primer mensaje"""
        pass
    
    @abstractmethod
    def process_response(self, user_input: str) -> Dict[str, Any]:
        """Procesa la respuesta del usuario"""
        pass
    
    def is_completed(self) -> bool:
        """Verifica si el flujo está completado"""
        return self.conversation.current_step >= self.conversation.total_steps


class ManualFlowHandler(BaseFlowHandler):
    """Manejador para el flujo manual con formulario Django"""
    
    def __init__(self, conversation: Conversation, form_class):
        super().__init__(conversation)
        self.form_class = form_class
        self._init_form()
    
    def _init_form(self):
        """Inicializa el formulario y filtra campos heredados"""
        self.form = self.form_class()
        self.fields = [
            (name, field) for name, field in self.form.fields.items()
            if "Campo heredado" not in str(field.label)
        ]
    
    def start(self) -> str:
        self.conversation.state = ConversationState.MANUAL_FLOW
        self.conversation.flow_type = "manual"
        self.conversation.current_step = 0
        self.conversation.total_steps = len(self.fields)
        self.conversation.collected_data = {}
        self.conversation.save()
        
        return f"✅ Perfecto, empecemos con el flujo manual.\n\n{self.get_current_question()}"
    
    def get_current_question(self) -> str:
        """Obtiene la pregunta actual con su ejemplo"""
        if self.is_completed():
            return ""
        
        field_name, field = self.fields[self.conversation.current_step]
        pregunta_data = generar_pregunta(field_name, field)
        pregunta_texto = pregunta_data["texto"]
        
        ejemplo = get_field_example(field_name, field)
        pregunta_con_ejemplo = f"{pregunta_texto}\n💡 Ejemplo: {ejemplo}"
        
        return pregunta_con_ejemplo
    
    def process_response(self, user_input: str) -> Dict[str, Any]:
        if self.is_completed():
            return {"message": "El flujo ya está completado.", "completed": True}
        
        field_name, field = self.fields[self.conversation.current_step]
        value = interpretar_respuesta(field, user_input)
        
        data = self.conversation.collected_data
        data[field_name] = convert_decimals(value)
        self.conversation.collected_data = convert_decimals(data)
        
        self.conversation.current_step += 1
        self.conversation.save()
        
        if self.is_completed():
            form = self.form_class(data=data)
            if form.is_valid():
                project_id = self._create_project_from_form_data(form.cleaned_data)
                self.conversation.mark_completed()
                
                message = self._generate_summary(form.cleaned_data)
                
                if project_id:
                    message += f"\n\n✅ **¡Proyecto creado exitosamente!**\n"
                    message += f"📁 Puedes verlo en el listado de proyectos\n"
                    message += f"🔗 ID del proyecto: {project_id}"
                
                return {
                    "message": message,
                    "completed": True,
                    "data": convert_decimals(form.cleaned_data),
                    "valid": True,
                    "project_id": project_id
                }
            else:
                return {
                    "message": self._generate_error_summary(form.errors),
                    "completed": True,
                    "data": convert_decimals(data),
                    "valid": False,
                    "errors": dict(form.errors)
                }
        
        return {
            "message": f"Perfecto 👍\n\n{self.get_current_question()}",
            "completed": False
        }
    
    def _create_project_from_form_data(self, cleaned_data: dict) -> Optional[int]:
        """Crea un proyecto desde datos del formulario"""
        try:
            from projects.models import Project
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            user = self.conversation.user or User.objects.filter(is_superuser=True).first()
            
            if not user:
                return None
            
            project = Project.objects.create(
                name=cleaned_data.get('name', 'Proyecto sin nombre'),
                location_address=cleaned_data.get('location_address', ''),
                description=cleaned_data.get('description', ''),
                creado_por=user,
                created_by_ai=False,
                estado=cleaned_data.get('estado', 'futuro'),
                imagen_proyecto=cleaned_data.get('imagen_proyecto'),
                ubicacion_proyecto=cleaned_data.get('ubicacion_proyecto', 'Medellin'),
                otra_ubicacion=cleaned_data.get('otra_ubicacion', ''),
                area_construida_total=cleaned_data.get('area_construida_total', Decimal('0')),
                numero_pisos=cleaned_data.get('numero_pisos', '1'),
                area_exterior_intervenir=cleaned_data.get('area_exterior_intervenir', Decimal('0')),
                built_area=cleaned_data.get('area_construida_total', Decimal('0')),
                exterior_area=cleaned_data.get('area_exterior_intervenir', Decimal('0')),
                columns_count=cleaned_data.get('columns_count', 0),
                walls_area=cleaned_data.get('walls_area', Decimal('0')),
                windows_area=cleaned_data.get('windows_area', Decimal('0')),
                doors_count=cleaned_data.get('doors_count', 0),
                doors_height=cleaned_data.get('doors_height', Decimal('2.1')),
                tipo_terreno=cleaned_data.get('tipo_terreno', 'normal'),
                acceso_obra=cleaned_data.get('acceso_obra', 'facil'),
                requiere_cerramiento=cleaned_data.get('requiere_cerramiento', False),
                sistema_entrepiso=cleaned_data.get('sistema_entrepiso', 'maciza'),
                exigencia_estructural=cleaned_data.get('exigencia_estructural', 'normal'),
                relacion_muros=cleaned_data.get('relacion_muros', 'media'),
                acabado_muros=cleaned_data.get('acabado_muros', 'estandar'),
                cielorrasos=cleaned_data.get('cielorrasos', 'parcial'),
                piso_zona_social=cleaned_data.get('piso_zona_social', 'ceramica'),
                piso_habitaciones=cleaned_data.get('piso_habitaciones', 'ceramica'),
                numero_banos=cleaned_data.get('numero_banos', 1),
                nivel_enchape_banos=cleaned_data.get('nivel_enchape_banos', 'medio'),
                puertas_interiores=cleaned_data.get('puertas_interiores', 0),
                puerta_principal_especial=cleaned_data.get('puerta_principal_especial', False),
                porcentaje_ventanas=cleaned_data.get('porcentaje_ventanas', 'medio'),
                metros_mueble_cocina=cleaned_data.get('metros_mueble_cocina', Decimal('0')),
                vestier_closets=cleaned_data.get('vestier_closets', 'ninguno'),
                calentador_gas=cleaned_data.get('calentador_gas', False),
                incluye_lavadero=cleaned_data.get('incluye_lavadero', False),
                punto_lavaplatos=cleaned_data.get('punto_lavaplatos', False),
                punto_lavadora=cleaned_data.get('punto_lavadora', False),
                punto_lavadero=cleaned_data.get('punto_lavadero', False),
                dotacion_electrica=cleaned_data.get('dotacion_electrica', 'estandar'),
                red_gas_natural=cleaned_data.get('red_gas_natural', False),
                tipo_cubierta=cleaned_data.get('tipo_cubierta', 'tradicional'),
                impermeabilizacion_adicional=cleaned_data.get('impermeabilizacion_adicional', False),
                area_adoquin=cleaned_data.get('area_adoquin', Decimal('0')),
                area_zonas_verdes=cleaned_data.get('area_zonas_verdes', Decimal('0')),
                incluir_estudios_disenos=cleaned_data.get('incluir_estudios_disenos', False),
                incluir_licencia_impuestos=cleaned_data.get('incluir_licencia_impuestos', False),
            )
            
            project.calculate_legacy_fields()
            project.presupuesto = project.calculate_final_budget()
            project.save()
            
            return project.id
            
        except Exception as e:
            print(f"❌ Error al crear proyecto: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_summary(self, cleaned_data: dict) -> str:
        summary = "✅ **Datos recopilados correctamente:**\n\n"
        for key, value in cleaned_data.items():
            label = key.replace('_', ' ').title()
            summary += f"• **{label}**: {value}\n"
        return summary
    
    def _generate_error_summary(self, errors: dict) -> str:
        summary = "⚠️ **Hay errores en los datos ingresados:**\n\n"
        for field, error_list in errors.items():
            summary += f"• **{field}**: {', '.join(error_list)}\n"
        return summary


class AIFlowHandler(BaseFlowHandler):
    """Manejador para el flujo con IA - preguntas naturales al cliente"""
    
    # ✅ 19 preguntas totales (todas en una sola lista)
    QUESTIONS = [
        {"question": "¿Qué tipo de construcción deseas hacer?", "example": "casa, local comercial, bodega"},
        {"question": "¿En qué ciudad o municipio estará ubicada la obra?", "example": "Medellín, Bogotá, Envigado"},
        {"question": "¿Cuál es el área aproximada a construir (en m²)?", "example": "120 m², 85.5 m², 200 m²"},
        {"question": "¿Cuántos pisos tendrá la construcción?", "example": "1, 2, 3 pisos"},
        {"question": "¿Cuántas habitaciones te gustaría?", "example": "3 habitaciones, 2 cuartos, 4 alcobas"},
        {"question": "¿Cuántos baños completos?", "example": "2 baños, 1 baño completo, 3 baños"},
        {"question": "🚗 ¿Cuántas plazas de garaje tiene el proyecto?", "example": "1 plaza, 2 garajes, 0 (sin garaje)"},
        {"question": "🌳 ¿Aproximadamente cuántos m² de zonas verdes tendrá?", "example": "30 m², 50 m², 0 (sin zonas verdes)"},
        {"question": "¿Qué nivel de acabados prefieres?", "example": "básico, estándar, premium"},
        {"question": "¿Quieres incluir cocina integral y clósets?", "example": "sí ambos, solo cocina integral, solo clósets, no"},
        {"question": "¿Cuál es tu presupuesto máximo o rango esperado? (opcional)", "example": "150 millones, entre 80-100 millones, no tengo definido"},
        {"question": "🎨 ¿Qué tipo de piso prefieres en la zona social?", "example": "cerámica, porcelanato, madera, mármol"},
        {"question": "🚪 ¿Deseas una puerta principal especial (madera fina, blindada)?", "example": "sí quiero puerta de madera fina, puerta blindada, no (puerta estándar)"},
        {"question": "💡 ¿Qué nivel de dotación eléctrica necesitas?", "example": "básica (puntos esenciales), estándar (normal), completa (domótica, luces LED)"},
        {"question": "🏠 ¿Qué tipo de cubierta prefieres?", "example": "tradicional en fibrocemento, teja de barro, concreto"},
        {"question": "🔧 ¿Necesitas instalaciones especiales?", "example": "calentador de gas, sistema de riego, gas natural, ninguna especial"},
        {"question": "📋 ¿Deseas incluir estudios, diseños y licencias en el presupuesto?", "example": "sí incluir todo, solo licencias, no (ya los tengo)"},
        {"question": "🚿 ¿Qué nivel de acabados en baños deseas?", "example": "bajo (enchape hasta 1.5m), medio (enchape completo), alto (porcelanato y grifería premium)"},
        {"question": "🪟 ¿Qué porcentaje aproximado de ventanas tendrá la construcción?", "example": "bajo (10-15% del área), medio (15-25%), alto (más del 25%)"},
    ]
    
    def __init__(self, conversation: Conversation, llm_client, budget_estimator=None):
        super().__init__(conversation)
        self.llm_client = llm_client
        self.budget_estimator = budget_estimator
    
    def start(self) -> str:
        self.conversation.state = ConversationState.AI_FLOW
        self.conversation.flow_type = "ai"
        self.conversation.current_step = 0
        self.conversation.total_steps = len(self.QUESTIONS)
        self.conversation.collected_data = {
            "answers": []
        }
        self.conversation.save()
        
        first_q = self.format_question_with_example(self.QUESTIONS[0])
        return f"🧠 **Modo IA activado**\n\nVoy a hacerte {len(self.QUESTIONS)} preguntas para generar tu presupuesto.\n\n{first_q}"
    
    def format_question_with_example(self, question_obj: dict) -> str:
        return f"{question_obj['question']}\n💡 Ejemplo: {question_obj['example']}"
    
    def get_current_question(self) -> str:
        if self.is_completed():
            return ""
        
        if self.conversation.current_step < len(self.QUESTIONS):
            return self.format_question_with_example(self.QUESTIONS[self.conversation.current_step])
        
        return ""
    
    def process_response(self, user_input: str) -> Dict[str, Any]:
        """Procesa respuesta del usuario"""
        
        if self.is_completed():
            return self._finalize_budget()
        
        data = self.conversation.collected_data
        answers = data.get("answers", [])
        
        # Guardar respuesta actual
        answers.append({
            "question": self.QUESTIONS[self.conversation.current_step]["question"],
            "answer": user_input.strip()
        })
        
        data["answers"] = answers
        self.conversation.collected_data = convert_decimals(data)
        self.conversation.current_step += 1
        self.conversation.save()
        
        # Verificar si terminamos
        if self.conversation.current_step >= len(self.QUESTIONS):
            return self._finalize_budget()
        
        # Siguiente pregunta
        progress = f"[{self.conversation.current_step}/{len(self.QUESTIONS)}]"
        return {
            "message": f"{progress} {self.get_current_question()}",
            "completed": False
        }

    def _finalize_budget(self) -> Dict[str, Any]:
        """Genera el presupuesto final"""
        project_id, project_budget = self._create_project_from_ai_data(
            self.conversation.collected_data
        )
        
        if project_id and project_budget:
            budget = self._generate_ai_budget_with_real_cost(
                self.conversation.collected_data["answers"],
                project_budget
            )
            
            budget += f"\n\n✅ **¡Proyecto creado exitosamente!**\n"
            budget += f"📁 Puedes verlo en: [Ver proyecto](/projects/{project_id}/)\n"
            budget += f"🔗 ID del proyecto: {project_id}"
        else:
            budget = self._generate_ai_budget()
            budget += f"\n\n⚠️ No se pudo crear el proyecto automáticamente."
        
        self.conversation.mark_completed()
        return {
            "message": budget,
            "completed": True,
            "data": convert_decimals(self.conversation.collected_data),
            "project_id": project_id
        }
    
    def _generate_ai_budget(self) -> str:
        """Genera el presupuesto usando IA"""
        answers = self.conversation.collected_data["answers"]
        
        if self.budget_estimator:
            try:
                datos_estimacion = self._convert_answers_to_estimation_data(answers)
                estimation = self.budget_estimator(datos_estimacion)
                return self._format_budget_estimation(estimation, datos_estimacion)
            except Exception as e:
                print(f"⚠️ Error en estimación: {e}")
        
        if not self.llm_client:
            return "⚠️ No hay conexión con el modelo de IA para generar el presupuesto."
        
        qa_text = "\n".join(f"P: {item['question']}\nR: {item['answer']}" for item in answers)
        
        system_prompt = """Eres un experto en presupuestos de construcción en Colombia.
        Genera un presupuesto detallado y profesional basado en las respuestas del cliente.
        
        Incluye:
        1️⃣ Resumen del proyecto
        2️⃣ Estimación de costos (materiales, mano de obra, total en COP)
        3️⃣ Recomendaciones técnicas
        
        Sé claro, técnico y realista."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Respuestas del cliente:\n\n{qa_text}\n\nGenera el presupuesto completo."}
        ]
        
        try:
            return self.llm_client.complete(messages)
        except Exception as e:
            return f"⚠️ Error al generar presupuesto: {str(e)}"
    
    def _convert_answers_to_estimation_data(self, answers: list) -> dict:
        """Convierte las respuestas en formato para el estimador"""
        data = {}
        
        # 🆕 MAPEO ACTUALIZADO CON GARAJES Y ZONAS VERDES SEPARADOS
        mapping = {
            0: ("tipo_construccion", str),
            1: ("ubicacion_proyecto", str),
            2: ("area_construida_total", float),
            3: ("numero_pisos", int),
            4: ("habitaciones", int),
            5: ("banos", int),
            6: ("plazas_garaje", int),           # 🆕 GARAJES
            7: ("area_zonas_verdes", float),     # 🆕 ZONAS VERDES
            8: ("acabado_muros", str),
            9: ("cocina_closets", str),
            10: ("presupuesto_max", str),
            11: ("piso_zona_social", str),
            12: ("puerta_principal_especial", str),
            13: ("dotacion_electrica", str),
            14: ("tipo_cubierta", str),
            15: ("instalaciones_especiales", str),
            16: ("incluir_estudios_licencias", str),
            17: ("nivel_enchape_banos", str),
            18: ("porcentaje_ventanas", str),

        }
        
        import re
        for i, item in enumerate(answers):
            if i in mapping:
                field_name, field_type = mapping[i]
                try:
                    if field_type == float:
                        match = re.search(r'(\d+(?:\.\d+)?)', item['answer'])
                        data[field_name] = float(match.group(1)) if match else 0
                    elif field_type == int:
                        match = re.search(r'(\d+)', item['answer'])
                        data[field_name] = int(match.group(1)) if match else 0
                    else:
                        data[field_name] = item['answer']
                except:
                    data[field_name] = item['answer']
        
        return data
    
    def _format_budget_estimation(self, estimation: dict, datos: dict) -> str:
        """Formatea la estimación del presupuesto"""
        total = estimation.get("total_estimated_cop", 0)
        cost_m2 = estimation.get("cost_per_m2_cop", 0)
        confidence = estimation.get("confidence", 0)
        rationale = estimation.get("rationale", "")
        breakdown = estimation.get("breakdown", [])
        
        def format_cop(value):
            if isinstance(value, Decimal):
                value = float(value)
            return f"${value:,.0f}".replace(",", ".")
        
        result = "🏗️ **PRESUPUESTO ESTIMADO**\n\n"
        result += "📊 **RESUMEN DEL PROYECTO**\n"
        result += f"• Tipo: {datos.get('tipo_construccion', 'N/A')}\n"
        result += f"• Ubicación: {datos.get('ubicacion_proyecto', 'N/A')}\n"
        result += f"• Área: {datos.get('area_construida_total', 0)} m²\n"
        result += f"• Pisos: {datos.get('numero_pisos', 1)}\n"
        result += f"• 🚗 Garajes: {datos.get('plazas_garaje', 0)} {'plaza' if datos.get('plazas_garaje', 0) == 1 else 'plazas'}\n"
        result += f"• 🌳 Zonas verdes: {datos.get('area_zonas_verdes', 0)} m²\n"
        result += f"• Acabados: {datos.get('acabado_muros', 'N/A')}\n"
        result += f"• Piso zona social: {datos.get('piso_zona_social', 'N/A')}\n"
        result += f"• Puerta principal especial: {datos.get('puerta_principal_especial', 'N/A')}\n\n"
        result += f"• Dotación eléctrica: {datos.get('dotacion_electrica', 'N/A')}\n"
        result += f"• Tipo de cubierta: {datos.get('tipo_cubierta', 'N/A')}\n\n"
        result += f"• Instalaciones especiales: {datos.get('instalaciones_especiales', 'N/A')}\n"
        result += f"• Incluir estudios y licencias: {datos.get('incluir_estudios_licencias', 'N/A')}\n\n"
        result += f"• Nivel de enchape baños: {datos.get('nivel_enchape_banos', 'N/A')}\n"
        result += f"• Porcentaje de ventanas: {datos.get('porcentaje_ventanas', 'N/A')}\n\n"

        
        result += "💰 **ESTIMACIÓN DE COSTOS**\n"
        result += f"• **Costo total estimado**: {format_cop(total)} COP\n"
        result += f"• **Costo por m²**: {format_cop(cost_m2)} COP/m²\n"
        result += f"• **Nivel de confianza**: {confidence}%\n\n"
        
        if breakdown:
            result += "📋 **DESGLOSE POR FACTORES**\n"
            for item in breakdown:
                factor = item.get("factor", "")
                impact_pct = item.get("impact_pct", 0)
                impact_cop = item.get("impact_cop", 0)
                if impact_cop > 0:
                    result += f"• {factor}: +{impact_pct}% ({format_cop(impact_cop)} COP)\n"
            result += "\n"
        
        if rationale:
            result += f"💡 **ANÁLISIS**\n{rationale}\n\n"
        
        result += "⚠️ *Nota: Esta es una estimación preliminar. Se recomienda una evaluación técnica detallada para un presupuesto definitivo.*"
        
        return result
    
    def _generate_ai_budget_with_real_cost(self, answers: list, project_budget: Decimal) -> str:
        """Genera el mensaje de presupuesto usando el costo real calculado del proyecto"""
        
        # ✅ Acceso corregido a índices (0-18)
        tipo_construccion = answers[0]["answer"] if len(answers) > 0 else "Casa"
        ubicacion = answers[1]["answer"] if len(answers) > 1 else "Medellín"
        area_str = answers[2]["answer"] if len(answers) > 2 else "0"
        pisos = answers[3]["answer"] if len(answers) > 3 else "1"
        habitaciones = answers[4]["answer"] if len(answers) > 4 else "3"
        banos = answers[5]["answer"] if len(answers) > 5 else "2"
        garajes = answers[6]["answer"] if len(answers) > 6 else "0"
        zonas_verdes = answers[7]["answer"] if len(answers) > 7 else "0"
        acabados = answers[8]["answer"] if len(answers) > 8 else "estándar"
        cocina_closets = answers[9]["answer"] if len(answers) > 9 else "sí"
        presupuesto_max = answers[10]["answer"] if len(answers) > 10 else ""
        piso_zona_social = answers[11]["answer"] if len(answers) > 11 else "ceramica"
        puerta_especial = answers[12]["answer"] if len(answers) > 12 else "no"  # ✅ CORREGIDO: era puerta_principal_especial
        dotacion_electrica = answers[13]["answer"] if len(answers) > 13 else "estándar"
        tipo_cubierta = answers[14]["answer"] if len(answers) > 14 else "tradicional"
        instalaciones_especiales = answers[15]["answer"] if len(answers) > 15 else ""
        incluir_estudios = answers[16]["answer"] if len(answers) > 16 else "no"
        nivel_banos = answers[17]["answer"] if len(answers) > 17 else "medio"
        porcentaje_ventanas = answers[18]["answer"] if len(answers) > 18 else "medio"
        
        import re
        area_match = re.search(r'(\d+(?:\.\d+)?)', area_str)
        area = float(area_match.group(1)) if area_match else 100
        
        garajes_match = re.search(r'(\d+)', str(garajes))
        num_garajes = int(garajes_match.group(1)) if garajes_match else 0
        
        zonas_match = re.search(r'(\d+(?:\.\d+)?)', str(zonas_verdes))
        area_zonas = float(zonas_match.group(1)) if zonas_match else 0
        
        budget_float = float(project_budget)
        cost_per_m2 = budget_float / area if area > 0 else 0
        
        # 🆕 DETECTAR CARACTERÍSTICAS PREMIUM (con variable corregida)
        tiene_marmol = "marmol" in piso_zona_social.lower() or "mármol" in piso_zona_social.lower() or "granito" in piso_zona_social.lower()
        tiene_riego = "riego" in instalaciones_especiales.lower()
        ventanas_alto = "alto" in porcentaje_ventanas.lower()
        puerta_blindada = "blindada" in puerta_especial.lower()  # ✅ CORREGIDO
        
        def format_cop(value):
            if isinstance(value, Decimal):
                value = float(value)
            return f"${value:,.0f}".replace(",", ".")
        
        result = "🏗️ **PRESUPUESTO CALCULADO**\n\n"
        result += "📊 **RESUMEN DEL PROYECTO**\n"
        result += f"• Tipo: {tipo_construccion}\n"
        result += f"• Ubicación: {ubicacion}\n"
        result += f"• Área construida: {area} m²\n"
        result += f"• Pisos: {pisos}\n"
        result += f"• Habitaciones: {habitaciones}\n"
        result += f"• Baños: {banos}\n"
        result += f"• 🚗 Garajes: {num_garajes} {'plaza' if num_garajes == 1 else 'plazas'}\n"
        result += f"• 🌳 Zonas verdes: {area_zonas} m²\n"
        result += f"• Acabados: {acabados}\n"
        
        # 🆕 AGREGAR SECCIÓN DE CARACTERÍSTICAS PREMIUM
        if tiene_marmol or tiene_riego or ventanas_alto or puerta_blindada:
            result += f"\n🌟 **CARACTERÍSTICAS PREMIUM INCLUIDAS:**\n"
            if tiene_marmol:
                result += f"  • Piso de mármol/granito en zona social (+$300.000/m²)\n"
            if tiene_riego:
                result += f"  • Sistema de riego automatizado para zonas verdes\n"
            if ventanas_alto:
                result += f"  • Alto porcentaje de ventanas (25%+ del área)\n"
            if puerta_blindada:
                result += f"  • Puerta principal blindada premium\n"
        
        result += f"\n• Dotación eléctrica: {dotacion_electrica}\n"
        result += f"• Tipo de cubierta: {tipo_cubierta}\n\n"
        
        result += "💰 **COSTO TOTAL DEL PROYECTO**\n"
        result += f"• **Presupuesto total**: {format_cop(budget_float)} COP\n"
        result += f"• **Costo por m²**: {format_cop(cost_per_m2)} COP/m²\n\n"
        
        result += "✨ **DETALLES INCLUIDOS**\n"
        result += "• Preliminares y movimiento de tierras\n"
        result += "• Cimentación y estructura\n"
        result += "• Mampostería y acabados\n"
        result += "• Instalaciones hidrosanitarias\n"
        result += "• Instalaciones eléctricas\n"
        result += "• Carpintería y herrería\n"
        
        if num_garajes > 0:
            result += f"• 🚗 Garaje para {num_garajes} {'vehículo' if num_garajes == 1 else 'vehículos'} (aprox. {format_cop(num_garajes * 12000000)} COP)\n"
        
        if area_zonas > 0:
            costo_zonas = area_zonas * 120000
            if tiene_riego:
                costo_zonas += area_zonas * 80000
            result += f"• 🌳 Zonas verdes y paisajismo {area_zonas} m²"
            if tiene_riego:
                result += f" con riego automatizado"
            result += f" (aprox. {format_cop(costo_zonas)} COP)\n"
        
        if tiene_marmol:
            result += f"• 🪨 Piso de mármol/granito en zona social (aprox. {format_cop(area * 300000)} COP)\n"
        
        if ventanas_alto:
            result += f"• 🪟 Ventanería premium (25%+ del área) (aprox. {format_cop(area * 150000)} COP)\n"
        
        if puerta_blindada:
            result += f"• 🚪 Puerta principal blindada de alta seguridad (aprox. {format_cop(8000000)} COP)\n"
        
        result += "• Cubierta y acabados finales\n"
        result += "• Estudios, diseños y licencias\n\n"
        
        result += "💡 **NOTA IMPORTANTE**\n"
        result += "Este presupuesto fue calculado con base en:\n"
        result += f"• Análisis detallado de {area} m² de construcción\n"
        
        if num_garajes > 0:
            result += f"• Inclusión de {num_garajes} {'plaza' if num_garajes == 1 else 'plazas'} de garaje\n"
        
        if area_zonas > 0:
            result += f"• Adecuación de {area_zonas} m² de zonas verdes\n"
        
        result += f"• Acabados nivel {acabados}\n"
        result += f"• Ubicación en {ubicacion}\n"
        result += "• Costos actualizados de materiales y mano de obra\n\n"
        
        result += "⚠️ *Este es un presupuesto paramétrico basado en proyectos similares. "
        result += "Para un presupuesto definitivo, se recomienda realizar un análisis de precios unitarios detallado.*"
        
        return result
    
    def _create_project_from_ai_data(self, datos: dict) -> Tuple[Optional[int], Optional[Decimal]]:
        """Crea un proyecto con los datos recopilados"""
        try:
            from projects.models import Project
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            user = self.conversation.user or User.objects.filter(is_superuser=True).first()
            
            if not user:
                print("❌ No hay usuario disponible")
                return None, None
            
            answers = datos.get("answers", [])
            
            # ✅ Extraer respuestas con índices correctos (0-18)
            tipo_construccion = answers[0]["answer"] if len(answers) > 0 else "Casa"
            ubicacion = answers[1]["answer"] if len(answers) > 1 else "Medellín"
            area_str = answers[2]["answer"] if len(answers) > 2 else "0"
            pisos = answers[3]["answer"] if len(answers) > 3 else "1"
            habitaciones = answers[4]["answer"] if len(answers) > 4 else "3"
            banos = answers[5]["answer"] if len(answers) > 5 else "2"
            garajes = answers[6]["answer"] if len(answers) > 6 else "0"
            zonas_verdes = answers[7]["answer"] if len(answers) > 7 else "0"
            acabados = answers[8]["answer"] if len(answers) > 8 else "estándar"
            cocina_closets = answers[9]["answer"] if len(answers) > 9 else "sí"
            presupuesto_max = answers[10]["answer"] if len(answers) > 10 else ""
            piso_social = answers[11]["answer"] if len(answers) > 11 else "ceramica"
            puerta_especial = answers[12]["answer"] if len(answers) > 12 else "no"
            dotacion_electrica = answers[13]["answer"] if len(answers) > 13 else "estándar"
            tipo_cubierta = answers[14]["answer"] if len(answers) > 14 else "tradicional"
            instalaciones_especiales = answers[15]["answer"] if len(answers) > 15 else ""
            incluir_estudios = answers[16]["answer"] if len(answers) > 16 else "no"
            nivel_banos = answers[17]["answer"] if len(answers) > 17 else "medio"
            porcentaje_ventanas = answers[18]["answer"] if len(answers) > 18 else "medio"
            
            import re
            area_match = re.search(r'(\d+(?:\.\d+)?)', area_str)
            area = Decimal(area_match.group(1)) if area_match else Decimal('100')
            
            garajes_match = re.search(r'(\d+)', str(garajes))
            num_garajes = int(garajes_match.group(1)) if garajes_match else 0
            
            zonas_match = re.search(r'(\d+(?:\.\d+)?)', str(zonas_verdes))
            area_zonas = Decimal(zonas_match.group(1)) if zonas_match else Decimal('0')
            
            # 🆕 VALIDACIÓN: Limitar pisos a rango razonable
            pisos_match = re.search(r'(\d+)', str(pisos))
            if pisos_match:
                num_pisos = int(pisos_match.group(1))
                if num_pisos > 5:
                    print(f"⚠️ ADVERTENCIA: Usuario indicó {num_pisos} pisos. Limitando a 3.")
                    pisos = "3"
            
            pisos_numero = "1"
            if any(word in pisos.lower() for word in ["2", "dos"]):
                pisos_numero = "2"
            elif any(word in pisos.lower() for word in ["3", "tres", "más", "mas"]):
                pisos_numero = "3_mas"
            
            acabados_norm = "estandar"
            if "básico" in acabados.lower() or "basico" in acabados.lower():
                acabados_norm = "basico"
            elif "premium" in acabados.lower() or "lujo" in acabados.lower():
                acabados_norm = "premium"
            
            banos_match = re.search(r'(\d+)', str(banos))
            numero_banos = int(banos_match.group(1)) if banos_match else 2
            
            # Piso zona social
            piso_social_norm = "ceramica"
            piso_social_lower = piso_social.lower()
            if "marmol" in piso_social_lower or "mármol" in piso_social_lower or "granito" in piso_social_lower:
                piso_social_norm = "madera"
                print(f"⚠️ Mármol/Granito detectado → usando 'madera' como acabado premium")
            elif "porcelanato" in piso_social_lower:
                piso_social_norm = "porcelanato"
            elif "madera" in piso_social_lower:
                piso_social_norm = "madera"
            
            # Puerta principal especial
            puerta_especial_bool = any(word in puerta_especial.lower() for word in ["sí", "si", "blindada", "fina", "especial"])
            
            # Dotación eléctrica
            dotacion_norm = "estandar"
            if "básica" in dotacion_electrica.lower() or "basica" in dotacion_electrica.lower():
                dotacion_norm = "basica"
            elif "completa" in dotacion_electrica.lower() or "domótica" in dotacion_electrica.lower():
                dotacion_norm = "completa"
            
            # Tipo de cubierta
            cubierta_norm = "tradicional"
            if "teja" in tipo_cubierta.lower():
                cubierta_norm = "teja"
            elif "concreto" in tipo_cubierta.lower():
                cubierta_norm = "concreto"
            
            # Instalaciones especiales
            tiene_calentador = "calentador" in instalaciones_especiales.lower()
            tiene_gas = "gas" in instalaciones_especiales.lower()
            tiene_riego = "riego" in instalaciones_especiales.lower()
            
            # Estudios y licencias
            incluir_estudios_bool = any(word in incluir_estudios.lower() for word in ["sí", "si", "todo"])
            
            # Nivel baños
            nivel_banos_norm = "medio"
            if "bajo" in nivel_banos.lower():
                nivel_banos_norm = "bajo"
            elif "alto" in nivel_banos.lower() or "premium" in nivel_banos.lower():
                nivel_banos_norm = "alto"
            
            # Porcentaje ventanas
            ventanas_norm = "medio"
            if "bajo" in porcentaje_ventanas.lower():
                ventanas_norm = "bajo"
            elif "alto" in porcentaje_ventanas.lower():
                ventanas_norm = "alto"
            
            # 🆕 CALCULAR AJUSTES PREMIUM ADICIONALES
            ajustes_premium = []
            costo_adicional_premium = Decimal('0')
            
            # Ajuste por mármol/granito
            if "marmol" in piso_social.lower() or "mármol" in piso_social.lower() or "granito" in piso_social.lower():
                costo_adicional_premium += area * Decimal('300000')
                ajustes_premium.append("Piso mármol/granito")
            
            # Ajuste por sistema de riego
            if tiene_riego and area_zonas > 0:
                costo_adicional_premium += area_zonas * Decimal('80000')
                ajustes_premium.append("Sistema de riego automatizado")
            
            # Ajuste por ventanas alto porcentaje
            if ventanas_norm == "alto":
                costo_adicional_premium += area * Decimal('150000')
                ajustes_premium.append("Alto porcentaje de ventanas")
            
            # Ajuste por puerta blindada premium
            if puerta_especial_bool and "blindada" in puerta_especial.lower():
                costo_adicional_premium += Decimal('8000000')
                ajustes_premium.append("Puerta blindada premium")
            
            print(f"🎨 Configuración extendida aplicada:")
            print(f"   - Piso social: {piso_social_norm} (original: {piso_social})")
            print(f"   - Puerta especial: {puerta_especial_bool}")
            print(f"   - Dotación eléctrica: {dotacion_norm}")
            print(f"   - Cubierta: {cubierta_norm}")
            print(f"   - Nivel baños: {nivel_banos_norm}")
            print(f"   - Ventanas: {ventanas_norm}")
            print(f"   - Sistema de riego: {tiene_riego}")
            if ajustes_premium:
                print(f"   - Ajustes premium adicionales: {', '.join(ajustes_premium)}")
                print(f"   - Costo adicional premium: ${costo_adicional_premium:,.0f}")
            
            # Crear descripción mejorada
            description_premium = f"Proyecto creado automáticamente por IA.\n"
            description_premium += f"Tipo: {tipo_construccion}\n"
            description_premium += f"Área: {area} m²\n"
            description_premium += f"Pisos: {pisos}\n"
            description_premium += f"Habitaciones: {habitaciones}\n"
            description_premium += f"Baños: {banos}\n"
            description_premium += f"Garajes: {num_garajes}\n"
            description_premium += f"Zonas verdes: {area_zonas} m²\n"
            description_premium += f"Acabados: {acabados}\n"
            if ajustes_premium:
                description_premium += f"\n🌟 CARACTERÍSTICAS PREMIUM:\n"
                for ajuste in ajustes_premium:
                    description_premium += f"  - {ajuste}\n"
            
            project = Project.objects.create(
                name=f"{tipo_construccion} - Proyecto IA Premium",
                location_address=ubicacion,
                description=description_premium,
                creado_por=user,
                created_by_ai=True,
                estado="futuro",
                ubicacion_proyecto="Medellin" if "medell" in ubicacion.lower() else "Otra",
                otra_ubicacion=ubicacion if "medell" not in ubicacion.lower() else "",
                area_construida_total=area,
                numero_pisos=pisos_numero,
                area_exterior_intervenir=area * Decimal('0.3'),
                built_area=area,
                exterior_area=area * Decimal('0.3'),
                columns_count=max(4, int(area / 25)),
                walls_area=Decimal('0'),
                windows_area=Decimal('0'),
                doors_count=0,
                doors_height=Decimal('2.1'),
                acabado_muros=acabados_norm,
                cielorrasos="total" if dotacion_norm == "completa" else "parcial",
                piso_zona_social=piso_social_norm,
                piso_habitaciones=piso_social_norm if piso_social_norm == "madera" else "ceramica",
                numero_banos=numero_banos,
                nivel_enchape_banos=nivel_banos_norm,
                tipo_terreno="normal",
                acceso_obra="medio",
                sistema_entrepiso="maciza",
                exigencia_estructural="normal",
                relacion_muros="media",
                puertas_interiores=max(2, int(area / 30)),
                puerta_principal_especial=puerta_especial_bool,
                porcentaje_ventanas=ventanas_norm,
                metros_mueble_cocina=Decimal('6.0'),
                vestier_closets="basico" if "sí" in cocina_closets.lower() else "ninguno",
                calentador_gas=tiene_calentador,
                incluye_lavadero=True,
                punto_lavaplatos=True,
                punto_lavadora=True,
                punto_lavadero=True,
                dotacion_electrica=dotacion_norm,
                red_gas_natural=tiene_gas,
                tipo_cubierta=cubierta_norm,
                impermeabilizacion_adicional=False,
                area_adoquin=Decimal(str(num_garajes * 12)) if num_garajes > 0 else Decimal('0'),
                area_zonas_verdes=area_zonas,
                incluir_estudios_disenos=incluir_estudios_bool,
                incluir_licencia_impuestos=incluir_estudios_bool,
            )
            
            project.calculate_legacy_fields()
            
            # 🆕 CALCULAR PRESUPUESTO BASE Y AGREGAR AJUSTES PREMIUM
            presupuesto_base = project.calculate_final_budget()
            presupuesto_final = presupuesto_base + costo_adicional_premium
            
            project.presupuesto = presupuesto_final
            project.save()
            
            print(f"✅ Proyecto creado: {project.name} (ID: {project.id})")
            print(f"   Presupuesto BASE: ${presupuesto_base:,.0f}")
            if costo_adicional_premium > 0:
                print(f"   + Ajustes premium: ${costo_adicional_premium:,.0f}")
            print(f"   = Presupuesto FINAL: ${presupuesto_final:,.0f}")
            
            return project.id, presupuesto_final
        
        except Exception as e:
            print(f"❌ Error al crear proyecto: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None