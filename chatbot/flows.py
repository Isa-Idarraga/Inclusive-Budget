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

# --- 🧠 Preguntas para modo IA de presupuestos (cliente final) ---
AI_BUDGET_QUESTIONS = [
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

# --- Inicializar cliente LLM ---
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAIAdapter(api_key=openai_api_key) if openai_api_key else None
except Exception as e:
    client = None
    print(f"⚠️ OpenAI client not initialized: {e}")


@csrf_exempt
def chat_api(request):
    """API que maneja tanto el flujo guiado manual como el modo IA con preguntas naturales."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"success": False, "error": "Mensaje vacío."}, status=400)

        user = request.user if request.user.is_authenticated else None
        user_id = str(user.id if user else request.session.session_key)

        # Recuperar o crear conversación
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

        # --- Comando para cancelar ---
        if msg_lower in ["cancelar", "parar", "salir", "detener"]:
            for key in ["budget_flow", "budget_ai", "ai_question_index", "ai_answers"]:
                request.session.pop(key, None)
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": "✅ Proceso cancelado. Puedes iniciar uno nuevo cuando quieras."}]
            })

        # --- 🧱 Modo manual (flujo guiado tradicional sin campos heredados) ---
        if msg_lower in ["nuevo presupuesto", "crear presupuesto", "iniciar presupuesto"]:
            # Filtrar campos heredados del formulario
            form = PresupuestoForm()
            form.fields = {
                k: v for k, v in form.fields.items()
                if "Campo heredado" not in v.label
            }
            primera_pregunta = iniciar_conversacion(form.__class__, user_id)
            request.session["budget_flow"] = True
            for key in ["budget_ai", "ai_question_index", "ai_answers"]:
                request.session.pop(key, None)
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": f"Perfecto 👍 Empecemos un nuevo presupuesto manual.\n{primera_pregunta}"}]
            })

        # --- 🤖 Nuevo modo: Presupuesto con IA ---
        if "crear presupuesto con ia" in msg_lower or "presupuesto inteligente" in msg_lower:
            request.session["budget_ai"] = True
            request.session["ai_question_index"] = 0
            request.session["ai_answers"] = []
            request.session.pop("budget_flow", None)
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": f"🧠 Modo IA activado. {AI_BUDGET_QUESTIONS[0]}"}]
            })

        # --- 🧩 Proceso de preguntas IA ---
        if request.session.get("budget_ai"):
            index = request.session.get("ai_question_index", 0)
            answers = request.session.get("ai_answers", [])

            # Guardar respuesta
            if index < len(AI_BUDGET_QUESTIONS):
                answers.append(user_message)
                request.session["ai_answers"] = answers
                index += 1
                request.session["ai_question_index"] = index

            # Si quedan preguntas, hacer la siguiente
            if index < len(AI_BUDGET_QUESTIONS):
                next_q = AI_BUDGET_QUESTIONS[index]
                return JsonResponse({
                    "success": True,
                    "conversation_id": conversation.id,
                    "messages": [{"role": "assistant", "content": next_q}]
                })

            # Si ya se respondieron todas → generar presupuesto con IA
            request.session.pop("budget_ai", None)
            request.session.pop("ai_question_index", None)
            request.session.pop("ai_answers", None)

            context_data = get_context_data()
            system_prompt = f"""
            Eres un asistente experto en presupuestos de construcción.
            Genera un presupuesto estimado con base en las respuestas del cliente.

            Datos reales del sistema:
            - Materiales: {context_data["materiales"]}
            - Trabajadores: {context_data["trabajadores"]}

            Usa formato claro con:
            1️⃣ Resumen del proyecto
            2️⃣ Estimación de costos (materiales, mano de obra y total)
            3️⃣ Comentarios o recomendaciones breves

            Mantén un tono profesional, conciso y fácil de entender para un cliente no técnico.
            """

            user_context = "\n".join(
                f"{q} → {a}" for q, a in zip(AI_BUDGET_QUESTIONS, answers)
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Respuestas del cliente:\n{user_context}"}
            ]

            if not client:
                return JsonResponse({
                    "success": True,
                    "conversation_id": conversation.id,
                    "messages": [{"role": "assistant", "content": "⚠️ No hay conexión con el modelo de IA."}]
                })

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
                "messages": [{"role": "assistant", "content": bot_reply}]
            })

        # --- 💬 Chat normal (IA general) ---
        if not client:
            return JsonResponse({
                "success": True,
                "conversation_id": conversation.id,
                "messages": [{"role": "assistant", "content": "⚠️ No hay conexión con el modelo de IA."}]
            })

        context_data = get_context_data()
        system_prompt = f"""
        Eres un asistente experto en presupuestos y gestión de obras.
        Usa los datos reales del sistema:
        Proyectos: {context_data["proyectos"]}
        Materiales: {context_data["materiales"]}
        Trabajadores: {context_data["trabajadores"]}
        Sé claro, técnico y breve.
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
