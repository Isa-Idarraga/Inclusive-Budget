# chatbot/services/conversation_service.py
from typing import Dict, Any, Optional
from django.utils import timezone
from ..models import Conversation, Message, ConversationState
from ..flow_handlers import ManualFlowHandler, AIFlowHandler
from .budget_estimator import BudgetEstimator


class ConversationService:
    """Servicio centralizado para manejar conversaciones"""
    
    def __init__(self, llm_client=None, form_class=None):
        self.llm_client = llm_client
        self.form_class = form_class
        self.budget_estimator = BudgetEstimator() if llm_client else None
    
    def get_or_create_conversation(
        self, 
        conversation_id: Optional[int] = None, 
        user=None
    ) -> Conversation:
        """Obtiene o crea una conversación"""
        if conversation_id:
            conversation = Conversation.objects.filter(
                id=conversation_id
            ).first()
            if conversation:
                return conversation
        
        # Crear nueva conversación
        return Conversation.objects.create(
            user=user,
            title=f"Conversación {timezone.now().strftime('%d/%m/%Y %H:%M')}"
        )
    
    def add_message(
        self, 
        conversation: Conversation, 
        role: str, 
        content: str,
        meta: Dict = None
    ) -> Message:
        """Agrega un mensaje a la conversación"""
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            meta=meta or {"timestamp": timezone.now().isoformat()}
        )
    
    def start_manual_flow(self, conversation: Conversation) -> str:
        """Inicia el flujo manual"""
        if not self.form_class:
            return "⚠️ No hay formulario configurado para el flujo manual."
        
        handler = ManualFlowHandler(conversation, self.form_class)
        return handler.start()
    
    def start_ai_flow(self, conversation: Conversation) -> str:
        """Inicia el flujo con IA"""
        handler = AIFlowHandler(
            conversation, 
            self.llm_client,
            budget_estimator=self.budget_estimator.estimate if self.budget_estimator else None
        )
        return handler.start()
    
    def process_flow_message(
        self, 
        conversation: Conversation, 
        user_input: str
    ) -> Dict[str, Any]:
        """Procesa un mensaje dentro de un flujo activo"""
        
        if conversation.flow_type == "manual":
            if not self.form_class:
                return {
                    "message": "⚠️ No hay formulario configurado.",
                    "completed": True
                }
            handler = ManualFlowHandler(conversation, self.form_class)
            
        elif conversation.flow_type == "ai":
            handler = AIFlowHandler(
                conversation, 
                self.llm_client,
                budget_estimator=self.budget_estimator.estimate if self.budget_estimator else None
            )
        else:
            return {
                "message": "No hay un flujo activo.",
                "completed": True
            }
        
        return handler.process_response(user_input)
    
    def cancel_flow(self, conversation: Conversation) -> str:
        """Cancela el flujo actual"""
        conversation.reset()
        return "✅ Proceso cancelado. Puedes iniciar uno nuevo cuando quieras."
    
    def handle_normal_chat(
        self, 
        conversation: Conversation, 
        user_message: str,
        context_data: Dict = None
    ) -> str:
        """Maneja chat normal sin flujo"""
        
        if not self.llm_client:
            return "⚠️ No hay conexión con el modelo de IA."
        
        # Construir prompt del sistema
        system_prompt = self._build_system_prompt(context_data or {})
        
        # Obtener historial de mensajes (últimos 10 para no sobrecargar)
        messages = [{"role": "system", "content": system_prompt}]
        
        # Obtener los últimos 10 mensajes en orden cronológico
        # Django no soporta indexación negativa en QuerySets
        recent_messages = conversation.messages.all().order_by('-created_at')[:10]
        
        # Revertir para tener orden cronológico (del más antiguo al más reciente)
        for msg in reversed(recent_messages):
            if msg.role != "system":
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Generar respuesta
        try:
            return self.llm_client.complete(messages)
        except Exception as e:
            return f"⚠️ Error al generar respuesta: {str(e)}"
    
    def _build_system_prompt(self, context_data: Dict) -> str:
        """Construye el prompt del sistema con contexto"""
        prompt = """Eres un asistente experto en presupuestos y gestión de obras de construcción.

Puedes ayudar con:
- Crear presupuestos manuales (di "nuevo presupuesto" o "crear presupuesto")
- Crear presupuestos con IA (di "presupuesto con IA" o "presupuesto inteligente")
- Consultar información sobre proyectos, materiales y trabajadores
- Responder preguntas técnicas sobre construcción

Sé claro, profesional y conciso."""

        if context_data:
            prompt += f"\n\nDatos del sistema disponibles:"
            if "proyectos" in context_data and context_data["proyectos"]:
                prompt += f"\n- Proyectos: {len(context_data['proyectos'])} registrados"
            if "materiales" in context_data and context_data["materiales"]:
                prompt += f"\n- Materiales: {len(context_data['materiales'])} disponibles"
            if "trabajadores" in context_data and context_data["trabajadores"]:
                prompt += f"\n- Trabajadores: {len(context_data['trabajadores'])} activos"
        
        return prompt
    
    def detect_intent(self, message: str) -> str:
        """Detecta la intención del mensaje"""
        msg_lower = message.lower()
        
        # Comandos de cancelación
        if any(cmd in msg_lower for cmd in ["cancelar", "parar", "salir", "detener"]):
            return "cancel"
        
        # Iniciar flujo manual
        if any(cmd in msg_lower for cmd in ["nuevo presupuesto", "crear presupuesto", "iniciar presupuesto", "presupuesto manual"]):
            return "start_manual"
        
        # Iniciar flujo IA
        if any(cmd in msg_lower for cmd in ["ia", "inteligente", "presupuesto ia", "presupuesto con ia", "presupuesto inteligente", "con ia"]):
            return "start_ai"
        
        return "chat"