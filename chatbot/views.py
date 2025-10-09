import json
import os
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .services import get_context_data
from .llm import OpenAIAdapter
from .models import Conversation, Message

# Inicializar el cliente
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        client = OpenAIAdapter(api_key=openai_api_key)
    else:
        client = None
except Exception as e:
    client = None
    print(f"⚠️ OpenAI client not initialized: {e}")


@csrf_exempt
def chat_api(request):
    """API para manejar mensajes del chatbot"""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    if not client:
        return JsonResponse({
            "success": False,
            "error": "Chatbot no configurado. Asigna OPENAI_API_KEY en el .env"
        }, status=503)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "")
        user = request.user if request.user.is_authenticated else None

        # Crear conversación si no existe
        conversation_id = data.get("conversation_id")
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
        else:
            conversation = Conversation.objects.create(user=user, title="Nueva conversación")

        # Guardar mensaje del usuario
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
            meta={"timestamp": timezone.now().isoformat()}
        )

        # Obtener datos del sistema
        context_data = get_context_data()

        system_prompt = f"""
        Eres un asistente experto en presupuestos y gestión de obras de construcción.
        Usa los siguientes datos reales del sistema para responder:

        Proyectos: {context_data["proyectos"]}
        Materiales: {context_data["materiales"]}
        Trabajadores: {context_data["trabajadores"]}

        Sé claro, técnico y breve. Si algo no está en los datos, dilo con transparencia.
        """

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation.messages.all():
            messages.append({"role": msg.role, "content": msg.content})

        # Llamar al modelo
        bot_reply = client.complete(messages)

        # Guardar respuesta del asistente
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=bot_reply,
            meta={"timestamp": timezone.now().isoformat()}
        )

        # Estructura JSON enriquecida
        response_data = {
            "success": True,
            "conversation_id": conversation.id,
            "messages": [
                {
                    "role": "user",
                    "content": user_message,
                    "meta": {"timestamp": timezone.now().isoformat()}
                },
                {
                    "role": "assistant",
                    "content": bot_reply,
                    "meta": {"timestamp": timezone.now().isoformat()}
                }
            ]
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def chat_view(request):
    """Renderiza la página del chatbot"""
    return render(request, "chatbot/chat.html")
