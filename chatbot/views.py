# chatbot/views.py
import json
import os
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .models import Conversation
from .services.conversation_service import ConversationService
from .llm import OpenAIAdapter
from .helpers import get_context_data
from projects.forms import ProjectForm  


# Inicializar servicio con LLM
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm_client = OpenAIAdapter(api_key=openai_api_key) if openai_api_key else None
except Exception as e:
    llm_client = None
    print(f"⚠️ OpenAI client not initialized: {e}")

conversation_service = ConversationService(llm_client=llm_client, form_class=ProjectForm)


@csrf_exempt
def chat_api(request):
    """API principal del chatbot - simplificada y clara"""
    
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        # Parsear request
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return JsonResponse({
                "success": False, 
                "error": "Mensaje vacío."
            }, status=400)
        
        # Obtener usuario
        user = request.user if request.user.is_authenticated else None
        
        # Obtener o crear conversación
        conversation_id = data.get("conversation_id")
        conversation = conversation_service.get_or_create_conversation(
            conversation_id=conversation_id,
            user=user
        )
        
        # Guardar mensaje del usuario
        conversation_service.add_message(
            conversation=conversation,
            role="user",
            content=user_message
        )
        
        # Procesar mensaje (ahora retorna un dict)
        response = process_user_message(conversation, user_message)
        
        # Guardar respuesta del asistente
        conversation_service.add_message(
            conversation=conversation,
            role="assistant",
            content=response["message"]
        )
        
        # Retornar respuesta
        return JsonResponse({
            "success": True,
            "conversation_id": conversation.id,
            "messages": [
                {"role": "assistant", "content": response["message"]}
            ],
            "flow_active": conversation.is_active(),
            "flow_type": conversation.flow_type,
            "progress": {
                "current": conversation.current_step,
                "total": conversation.total_steps
            } if conversation.is_active() else None
        })
    
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }, status=500)


def process_user_message(conversation: Conversation, user_message: str) -> dict:
    """
    Procesa el mensaje del usuario y retorna la respuesta como diccionario
    """
    service = ConversationService(
        llm_client=OpenAIAdapter(api_key=openai_api_key),
        form_class=ProjectForm
    )
    
    # Detectar intención
    intent = service.detect_intent(user_message)
    
    # Si hay un flujo activo
    if conversation.is_active():
        # Comando de cancelar
        if intent == "cancel":
            message = service.cancel_flow(conversation)
            return {"message": message}
        
        # Procesar mensaje del flujo
        result = service.process_flow_message(conversation, user_message)
        
        # Si el flujo se completó
        if result.get("completed"):
            # ✅ YA NO PREGUNTAR "¿Deseas guardar?"
            # El proyecto se crea automáticamente
            return {"message": result["message"], "completed": True}
        
        return {"message": result["message"]}
    
    # No hay flujo activo - detectar comandos
    if intent == "start_manual":
        message = service.start_manual_flow(conversation)
        return {"message": message}
    
    if intent == "start_ai":
        message = service.start_ai_flow(conversation)
        return {"message": message}
    
    if intent == "cancel":
        return {"message": "No hay ningún proceso activo para cancelar."}
    
    # Chat normal con contexto
    context_data = {
        "proyectos": [],
        "materiales": [],
        "trabajadores": []
    }
    
    message = service.handle_normal_chat(conversation, user_message, context_data)
    return {"message": message}


def chat_view(request):
    """Renderiza la interfaz del chatbot"""
    return render(request, "chatbot/chat.html")


def conversation_list(request):
    """Lista las conversaciones del usuario"""
    user = request.user if request.user.is_authenticated else None
    
    conversations = Conversation.objects.filter(user=user).values(
        "id", "title", "state", "created_at", "updated_at"
    )
    
    return JsonResponse({
        "success": True,
        "conversations": list(conversations)
    })


def conversation_detail(request, conversation_id):
    """Obtiene el detalle completo de una conversación"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in conversation.messages.all()
        ]
        
        return JsonResponse({
            "success": True,
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "state": conversation.state,
                "flow_type": conversation.flow_type,
                "created_at": conversation.created_at.isoformat(),
                "messages": messages
            }
        })
    except Conversation.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Conversación no encontrada"
        }, status=404)