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
        """
        Procesa la respuesta del usuario
        Retorna: {
            "message": str,
            "completed": bool,
            "data": dict (opcional)
        }
        """
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
        # Filtrar campos heredados (los que tienen "Campo heredado" en el label)
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
        if self.is_completed():
            return ""
        
        field_name, field = self.fields[self.conversation.current_step]
        pregunta_data = generar_pregunta(field_name, field)
        return pregunta_data["texto"]
    
    def process_response(self, user_input: str) -> Dict[str, Any]:
        if self.is_completed():
            return {
                "message": "El flujo ya está completado.",
                "completed": True
            }
        
        # Obtener campo actual
        field_name, field = self.fields[self.conversation.current_step]
        
        # Interpretar respuesta usando tu lógica existente
        value = interpretar_respuesta(field, user_input)
        
        # Guardar respuesta (convertir Decimals)
        data = self.conversation.collected_data
        data[field_name] = convert_decimals(value)
        self.conversation.collected_data = convert_decimals(data)
        
        # Avanzar
        self.conversation.current_step += 1
        self.conversation.save()
        
        # Verificar si terminamos
        if self.is_completed():
            # Validar formulario
            form = self.form_class(data=data)
            if form.is_valid():
                # 🆕 CREAR EL PROYECTO AUTOMÁTICAMENTE
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
        
        # Siguiente pregunta
        return {
            "message": f"Perfecto 👍\n\n{self.get_current_question()}",
            "completed": False
        }
    
    def _create_project_from_form_data(self, cleaned_data: dict) -> Optional[int]:
        """
        Crea un proyecto en la base de datos con los datos del formulario manual
        Retorna el ID del proyecto creado o None si hay error
        """
        try:
            from projects.models import Project
            from decimal import Decimal
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Obtener usuario (usar el de la conversación o el primer superuser)
            user = self.conversation.user
            if not user:
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    print("❌ No hay usuario disponible para crear el proyecto")
                    return None
            
            # Crear el proyecto directamente con los datos del formulario
            project = Project.objects.create(
                # Información básica
                name=cleaned_data.get('name', 'Proyecto sin nombre'),
                location_address=cleaned_data.get('location_address', ''),
                description=cleaned_data.get('description', ''),
                
                # Usuario creador
                creado_por=user,
                
                # 🆕 NO marcar como creado por IA (este es manual)
                created_by_ai=False,
                
                # Estado
                estado=cleaned_data.get('estado', 'futuro'),
                
                # Imagen
                imagen_proyecto=cleaned_data.get('imagen_proyecto'),
                
                # Datos del cuestionario
                ubicacion_proyecto=cleaned_data.get('ubicacion_proyecto', 'Medellin'),
                otra_ubicacion=cleaned_data.get('otra_ubicacion', ''),
                area_construida_total=cleaned_data.get('area_construida_total', Decimal('0')),
                numero_pisos=cleaned_data.get('numero_pisos', '1'),
                area_exterior_intervenir=cleaned_data.get('area_exterior_intervenir', Decimal('0')),
                
                # Campos básicos requeridos
                built_area=cleaned_data.get('area_construida_total', Decimal('0')),
                exterior_area=cleaned_data.get('area_exterior_intervenir', Decimal('0')),
                columns_count=cleaned_data.get('columns_count', 0),
                walls_area=cleaned_data.get('walls_area', Decimal('0')),
                windows_area=cleaned_data.get('windows_area', Decimal('0')),
                doors_count=cleaned_data.get('doors_count', 0),
                doors_height=cleaned_data.get('doors_height', Decimal('2.1')),
                
                # Terreno y preliminares
                tipo_terreno=cleaned_data.get('tipo_terreno', 'normal'),
                acceso_obra=cleaned_data.get('acceso_obra', 'facil'),
                requiere_cerramiento=cleaned_data.get('requiere_cerramiento', False),
                
                # Estructura
                sistema_entrepiso=cleaned_data.get('sistema_entrepiso', 'maciza'),
                exigencia_estructural=cleaned_data.get('exigencia_estructural', 'normal'),
                
                # Muros y acabados
                relacion_muros=cleaned_data.get('relacion_muros', 'media'),
                acabado_muros=cleaned_data.get('acabado_muros', 'estandar'),
                cielorrasos=cleaned_data.get('cielorrasos', 'parcial'),
                
                # Pisos
                piso_zona_social=cleaned_data.get('piso_zona_social', 'ceramica'),
                piso_habitaciones=cleaned_data.get('piso_habitaciones', 'ceramica'),
                numero_banos=cleaned_data.get('numero_banos', 1),
                nivel_enchape_banos=cleaned_data.get('nivel_enchape_banos', 'medio'),
                
                # Carpinterías
                puertas_interiores=cleaned_data.get('puertas_interiores', 0),
                puerta_principal_especial=cleaned_data.get('puerta_principal_especial', False),
                porcentaje_ventanas=cleaned_data.get('porcentaje_ventanas', 'medio'),
                metros_mueble_cocina=cleaned_data.get('metros_mueble_cocina', Decimal('0')),
                vestier_closets=cleaned_data.get('vestier_closets', 'ninguno'),
                
                # Hidrosanitario
                calentador_gas=cleaned_data.get('calentador_gas', False),
                incluye_lavadero=cleaned_data.get('incluye_lavadero', False),
                punto_lavaplatos=cleaned_data.get('punto_lavaplatos', False),
                punto_lavadora=cleaned_data.get('punto_lavadora', False),
                punto_lavadero=cleaned_data.get('punto_lavadero', False),
                
                # Eléctrico
                dotacion_electrica=cleaned_data.get('dotacion_electrica', 'estandar'),
                red_gas_natural=cleaned_data.get('red_gas_natural', False),
                
                # Cubierta
                tipo_cubierta=cleaned_data.get('tipo_cubierta', 'tradicional'),
                impermeabilizacion_adicional=cleaned_data.get('impermeabilizacion_adicional', False),
                
                # Exteriores
                area_adoquin=cleaned_data.get('area_adoquin', Decimal('0')),
                area_zonas_verdes=cleaned_data.get('area_zonas_verdes', Decimal('0')),
                
                # Profesionales
                incluir_estudios_disenos=cleaned_data.get('incluir_estudios_disenos', False),
                incluir_licencia_impuestos=cleaned_data.get('incluir_licencia_impuestos', False),
            )
            
            # Calcular campos heredados y presupuesto
            project.calculate_legacy_fields()
            project.presupuesto = project.calculate_final_budget()
            project.save()
            
            print(f"✅ Proyecto creado exitosamente: {project.name} (ID: {project.id})")
            print(f"   Presupuesto calculado: ${project.presupuesto:,.0f}")
            
            return project.id
            
        except Exception as e:
            print(f"❌ Error al crear proyecto desde formulario manual: {str(e)}")
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
    
    QUESTIONS = [
        "¿Qué tipo de construcción deseas hacer? (casa, apartamento, local comercial, etc.)",
        "¿En qué ciudad o municipio estará ubicada la obra?",
        "¿Cuál es el área aproximada a construir (en m²)?",
        "¿Cuántos pisos tendrá la construcción?",
        "¿Cuántas habitaciones te gustaría?",
        "¿Cuántos baños completos?",
        "¿Deseas incluir garaje o zona verde?",
        "¿Qué nivel de acabados prefieres? (básico, estándar, premium)",
        "¿Quieres incluir cocina integral y clósets?",
        "¿Cuál es tu presupuesto máximo o rango esperado? (opcional)",
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
        self.conversation.collected_data = {"answers": []}
        self.conversation.save()
        
        return f"🧠 **Modo IA activado**\n\nVoy a hacerte {len(self.QUESTIONS)} preguntas para generar tu presupuesto.\n\n{self.get_current_question()}"
    
    def get_current_question(self) -> str:
        if self.is_completed():
            return ""
        return self.QUESTIONS[self.conversation.current_step]
    
    def process_response(self, user_input: str) -> Dict[str, Any]:
        if self.is_completed():
            return {
                "message": "El flujo ya está completado.",
                "completed": True
            }
        
        # Guardar respuesta
        answers = self.conversation.collected_data.get("answers", [])
        answers.append({
            "question": self.QUESTIONS[self.conversation.current_step],
            "answer": user_input.strip()
        })
        self.conversation.collected_data["answers"] = answers
        
        # Avanzar
        self.conversation.current_step += 1
        
        # Convertir Decimals antes de guardar
        self.conversation.collected_data = convert_decimals(self.conversation.collected_data)
        self.conversation.save()
        
        # Verificar si terminamos
        if self.is_completed():
            # 🆕 CREAR PROYECTO PRIMERO
            project_id, project_budget = self._create_project_from_ai_data(
                self.conversation.collected_data
            )
            
            # Generar el mensaje con el presupuesto real del proyecto
            if project_id and project_budget:
                budget = self._generate_ai_budget_with_real_cost(
                    self.conversation.collected_data["answers"],
                    project_budget
                )
                budget += f"\n\n✅ **¡Proyecto creado exitosamente!**\n"
                budget += f"📁 Puedes verlo en: [Ver proyecto](/projects/{project_id}/)\n"
                budget += f"🔗 ID del proyecto: {project_id}"
            else:
                # Fallback si no se pudo crear el proyecto
                budget = self._generate_ai_budget()
                budget += f"\n\n⚠️ No se pudo crear el proyecto automáticamente."
            
            self.conversation.mark_completed()
            return {
                "message": budget,
                "completed": True,
                "data": convert_decimals(self.conversation.collected_data),
                "project_id": project_id
            }
        
        # Siguiente pregunta
        progress = f"[{self.conversation.current_step}/{self.conversation.total_steps}]"
        return {
            "message": f"{progress} {self.get_current_question()}",
            "completed": False
        }
    
    def _generate_ai_budget(self) -> str:
        """Genera el presupuesto usando IA y el estimador si está disponible"""
        
        answers = self.conversation.collected_data["answers"]
        
        # Si hay estimador de presupuesto, usarlo
        if self.budget_estimator:
            try:
                # Convertir respuestas a formato del estimador
                datos_estimacion = self._convert_answers_to_estimation_data(answers)
                estimation = self.budget_estimator(datos_estimacion)
                
                # Formatear resultado
                return self._format_budget_estimation(estimation, datos_estimacion)
            except Exception as e:
                print(f"⚠️ Error en estimación: {e}")
                # Fallback a generación simple con LLM
        
        # Fallback: usar solo el LLM
        if not self.llm_client:
            return "⚠️ No hay conexión con el modelo de IA para generar el presupuesto."
        
        qa_text = "\n".join(
            f"P: {item['question']}\nR: {item['answer']}"
            for item in answers
        )
        
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
        
        # Mapeo de preguntas a campos del estimador
        mapping = {
            0: ("tipo_construccion", str),
            1: ("ubicacion_proyecto", str),
            2: ("area_construida_total", float),
            3: ("numero_pisos", int),
            4: ("habitaciones", int),
            5: ("banos", int),
            6: ("garaje_zona_verde", str),
            7: ("acabado_muros", str),
            8: ("cocina_closets", str),
            9: ("presupuesto_max", str),
        }
        
        for i, item in enumerate(answers):
            if i in mapping:
                field_name, field_type = mapping[i]
                try:
                    if field_type == float:
                        # Extraer números del texto
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)', item['answer'])
                        data[field_name] = float(match.group(1)) if match else 0
                    elif field_type == int:
                        match = re.search(r'(\d+)', item['answer'])
                        data[field_name] = int(match.group(1)) if match else 1
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
        
        # Formatear números colombianos
        def format_cop(value):
            # Convertir Decimal a float si es necesario
            if isinstance(value, Decimal):
                value = float(value)
            return f"${value:,.0f}".replace(",", ".")
        
        result = "🏗️ **PRESUPUESTO ESTIMADO**\n\n"
        result += "📊 **RESUMEN DEL PROYECTO**\n"
        result += f"• Tipo: {datos.get('tipo_construccion', 'N/A')}\n"
        result += f"• Ubicación: {datos.get('ubicacion_proyecto', 'N/A')}\n"
        result += f"• Área: {datos.get('area_construida_total', 0)} m²\n"
        result += f"• Pisos: {datos.get('numero_pisos', 1)}\n"
        result += f"• Acabados: {datos.get('acabado_muros', 'N/A')}\n\n"
        
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
        
        # Extraer datos de las respuestas
        tipo_construccion = answers[0]["answer"] if len(answers) > 0 else "Casa"
        ubicacion = answers[1]["answer"] if len(answers) > 1 else "Medellín"
        area_str = answers[2]["answer"] if len(answers) > 2 else "0"
        pisos = answers[3]["answer"] if len(answers) > 3 else "1"
        habitaciones = answers[4]["answer"] if len(answers) > 4 else "3"
        banos = answers[5]["answer"] if len(answers) > 5 else "2"
        acabados = answers[7]["answer"] if len(answers) > 7 else "estándar"
        
        # Extraer área
        import re
        area_match = re.search(r'(\d+(?:\.\d+)?)', area_str)
        area = float(area_match.group(1)) if area_match else 100
        
        # Calcular costo por m²
        budget_float = float(project_budget)
        cost_per_m2 = budget_float / area if area > 0 else 0
        
        # Formatear números
        def format_cop(value):
            if isinstance(value, Decimal):
                value = float(value)
            return f"${value:,.0f}".replace(",", ".")
        
        result = "🏗️ **PRESUPUESTO CALCULADO**\n\n"
        result += "📊 **RESUMEN DEL PROYECTO**\n"
        result += f"• Tipo: {tipo_construccion}\n"
        result += f"• Ubicación: {ubicacion}\n"
        result += f"• Área: {area} m²\n"
        result += f"• Pisos: {pisos}\n"
        result += f"• Habitaciones: {habitaciones}\n"
        result += f"• Baños: {banos}\n"
        result += f"• Acabados: {acabados}\n\n"
        
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
        result += "• Cubierta y acabados finales\n"
        result += "• Estudios, diseños y licencias\n\n"
        
        result += "💡 **NOTA IMPORTANTE**\n"
        result += "Este presupuesto fue calculado con base en:\n"
        result += f"• Análisis detallado de {area} m² de construcción\n"
        result += f"• Acabados nivel {acabados}\n"
        result += f"• Ubicación en {ubicacion}\n"
        result += "• Costos actualizados de materiales y mano de obra\n\n"
        
        result += "⚠️ *Este es un presupuesto paramétrico basado en proyectos similares. "
        result += "Para un presupuesto definitivo, se recomienda realizar un análisis de precios unitarios detallado.*"
        
        return result
    
    def _create_project_from_ai_data(self, datos: dict) -> Tuple[Optional[int], Optional[Decimal]]:
        """
        Crea un proyecto en la base de datos con los datos recopilados por la IA
        Retorna (project_id, project_budget) o (None, None) si hay error
        """
        try:
            from projects.models import Project
            from decimal import Decimal
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Obtener usuario (usar el de la conversación o el primer superuser)
            user = self.conversation.user
            if not user:
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    print("❌ No hay usuario disponible para crear el proyecto")
                    return None, None
            
            # Mapeo de respuestas a campos del modelo
            answers = self.conversation.collected_data.get("answers", [])
            
            # Extraer datos de las respuestas
            tipo_construccion = answers[0]["answer"] if len(answers) > 0 else "Casa"
            ubicacion = answers[1]["answer"] if len(answers) > 1 else "Medellín"
            area_str = answers[2]["answer"] if len(answers) > 2 else "0"
            pisos = answers[3]["answer"] if len(answers) > 3 else "1"
            habitaciones = answers[4]["answer"] if len(answers) > 4 else "3"
            banos = answers[5]["answer"] if len(answers) > 5 else "2"
            garaje = answers[6]["answer"] if len(answers) > 6 else "Sí"
            acabados = answers[7]["answer"] if len(answers) > 7 else "estándar"
            cocina_closets = answers[8]["answer"] if len(answers) > 8 else "Sí"
            presupuesto_max = answers[9]["answer"] if len(answers) > 9 else ""
            
            # Extraer área (números)
            import re
            area_match = re.search(r'(\d+(?:\.\d+)?)', area_str)
            area = Decimal(area_match.group(1)) if area_match else Decimal('100')
            
            # Normalizar número de pisos
            pisos_numero = "1"
            if any(word in pisos.lower() for word in ["2", "dos"]):
                pisos_numero = "2"
            elif any(word in pisos.lower() for word in ["3", "tres", "más", "mas"]):
                pisos_numero = "3_mas"
            
            # Normalizar acabados
            acabados_norm = "estandar"
            if "básico" in acabados.lower() or "basico" in acabados.lower():
                acabados_norm = "basico"
            elif "premium" in acabados.lower() or "lujo" in acabados.lower():
                acabados_norm = "premium"
            
            # Extraer número de baños
            banos_match = re.search(r'(\d+)', str(banos))
            numero_banos = int(banos_match.group(1)) if banos_match else 2
            
            # Crear el proyecto
            project = Project.objects.create(
                # Información básica
                name=f"{tipo_construccion} - Proyecto IA",
                location_address=ubicacion,
                description=f"Proyecto creado automáticamente por IA.\n"
                           f"Tipo: {tipo_construccion}\n"
                           f"Área: {area} m²\n"
                           f"Pisos: {pisos}\n"
                           f"Habitaciones: {habitaciones}\n"
                           f"Baños: {banos}\n"
                           f"Acabados: {acabados}",
                
                # Usuario creador
                creado_por=user,
                
                # 🆕 Marcar como creado por IA
                created_by_ai=True,
                
                # Estado
                estado="futuro",
                
                # Datos del cuestionario
                ubicacion_proyecto="Medellin" if "medell" in ubicacion.lower() else "Otra",
                otra_ubicacion=ubicacion if "medell" not in ubicacion.lower() else "",
                area_construida_total=area,
                numero_pisos=pisos_numero,
                area_exterior_intervenir=area * Decimal('0.3'),  # 30% del área
                
                # Campos básicos requeridos
                built_area=area,
                exterior_area=area * Decimal('0.3'),
                columns_count=max(4, int(area / 25)),
                walls_area=Decimal('0'),
                windows_area=Decimal('0'),
                doors_count=0,
                doors_height=Decimal('2.1'),
                
                # Acabados
                acabado_muros=acabados_norm,
                cielorrasos="parcial",
                piso_zona_social="porcelanato" if acabados_norm == "premium" else "ceramica",
                piso_habitaciones="porcelanato" if acabados_norm == "premium" else "ceramica",
                
                # Baños
                numero_banos=numero_banos,
                nivel_enchape_banos="medio",
                
                # Otros
                tipo_terreno="normal",
                acceso_obra="medio",
                sistema_entrepiso="maciza",
                exigencia_estructural="normal",
                relacion_muros="media",
                
                # Carpinterías
                puertas_interiores=max(2, int(area / 30)),
                puerta_principal_especial=False,
                porcentaje_ventanas="medio",
                metros_mueble_cocina=Decimal('6.0'),
                vestier_closets="basico" if "sí" in cocina_closets.lower() else "ninguno",
                
                # Hidrosanitario
                calentador_gas=True,
                incluye_lavadero=True,
                punto_lavaplatos=True,
                punto_lavadora=True,
                punto_lavadero=True,
                
                # Eléctrico
                dotacion_electrica="estandar",
                red_gas_natural=True,
                
                # Cubierta
                tipo_cubierta="tradicional",
                impermeabilizacion_adicional=False,
                
                # Exteriores
                area_adoquin=Decimal('0'),
                area_zonas_verdes=area * Decimal('0.2'),
                
                # Profesionales
                incluir_estudios_disenos=True,
                incluir_licencia_impuestos=True,
            )
            
            # Calcular campos heredados y presupuesto
            project.calculate_legacy_fields()
            project.presupuesto = project.calculate_final_budget()
            project.save()
            
            print(f"✅ Proyecto creado exitosamente: {project.name} (ID: {project.id})")
            print(f"   Presupuesto calculado: ${project.presupuesto:,.0f}")
            
            return project.id, project.presupuesto
            
        except Exception as e:
            print(f"❌ Error al crear proyecto desde datos de IA: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None