import json
import os
import traceback
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .models import Conversation, Message
from .services import get_context_data
from .llm import OpenAIAdapter
from .logic.chat_flow import iniciar_conversacion, procesar_respuesta
from projects.forms import ProjectForm as PresupuestoForm


# Inicializar cliente LLM (OpenAI o Groq)
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAIAdapter(api_key=openai_api_key) if openai_api_key else None
except Exception as e:
    client = None
    print(f"⚠️ OpenAI client not initialized: {e}")


@csrf_exempt
def chat_api(request):
    """API que maneja tanto el flujo guiado de presupuestos como las consultas con IA."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        # --- 🔹 Parsear entrada ---
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Formato JSON inválido."}, status=400)

        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"success": False, "error": "Mensaje vacío."}, status=400)

        user = request.user if request.user.is_authenticated else None
        user_id = str(user.id if user else request.session.session_key)

        # --- 🔹 Recuperar o crear conversación ---
        conversation_id = data.get("conversation_id")
        conversation = (
            Conversation.objects.filter(id=conversation_id, user=user).first()
            if conversation_id else Conversation.objects.create(user=user, title="Nueva conversación")
        )

        # Guardar mensaje del usuario
        Message.objects.create(
            conversation=conversation,
            role="user",
            content=user_message,
            meta={"timestamp": timezone.now().isoformat()}
        )

        msg_lower = user_message.lower()

        # --- 🔹 Comandos básicos ---
        if msg_lower in ["cancelar", "parar", "salir", "detener"]:
            request.session.pop("budget_flow", None)
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": "✅ Proceso cancelado. Puedes iniciar uno nuevo cuando quieras."}]
            })

        # --- 🔹 Inicio de flujo guiado ---
        if msg_lower in ["nuevo presupuesto", "crear presupuesto", "iniciar presupuesto"]:
            primera_pregunta = iniciar_conversacion(PresupuestoForm, user_id)
            request.session["budget_flow"] = True  # Activa modo guiado
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": f"Perfecto 👍 Empecemos.\n{primera_pregunta}"}]
            })

        # --- 🔹 Flujo guiado activo ---
        if request.session.get("budget_flow"):
            respuesta = procesar_respuesta(user_id, user_message)

            # Si ya terminó el formulario, salir del modo guiado
            if "Presupuesto completado" in respuesta or "🎯" in respuesta:
                request.session.pop("budget_flow", None)

            Message.objects.create(
                conversation=conversation,
                role="assistant",
                content=respuesta,
                meta={"timestamp": timezone.now().isoformat()}
            )

            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": respuesta}],
            })

        # --- 🔹 Modo normal con IA (si no está en flujo guiado) ---
        if not client:
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": "⚠️ No hay conexión con el modelo de IA. Configura OPENAI_API_KEY."}]
            })

        context_data = get_context_data()
        system_prompt = f"""
        Eres un asistente experto en presupuestos y gestión de obras.
        Usa los siguientes datos reales del sistema:

        Proyectos: {context_data["proyectos"]}
        Materiales: {context_data["materiales"]}
        Trabajadores: {context_data["trabajadores"]}

        Sé claro, técnico y breve. Si algo no está en los datos, dilo con transparencia.
        """

        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation.messages.all():
            messages.append({"role": msg.role, "content": msg.content})

        bot_reply = client.complete(messages)

        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=bot_reply,
            meta={"timestamp": timezone.now().isoformat()}
        )

        return JsonResponse({
            "success": True,
            "conversation_id": conversation.id,
            "messages": [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": bot_reply},
            ],
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "error": f"⚠️ Error interno: {str(e)}"
        }, status=200)


def chat_view(request):
    """Renderiza la interfaz del chatbot."""
    return render(request, "chatbot/chat.html")
