import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
# from groq import Groq  # Comentado temporalmente  
from .services import get_context_data  

# Cliente Groq - hacer opcional para no bloquear el proyecto
try:
    # groq_api_key = os.getenv("GROQ_API_KEY")
    # if groq_api_key:
    #     client = Groq(api_key=groq_api_key)
    # else:
    #     client = None
    client = None  # Comentado temporalmente
except Exception as e:
    client = None
    print(f"Warning: Groq client not initialized: {e}")

@csrf_exempt
def chat_api(request):
    """API que recibe mensajes del frontend y responde con Groq"""
    if request.method == "POST":
        if not client:
            return JsonResponse({
                "response": "El chatbot no está configurado. Por favor configure GROQ_API_KEY en el archivo .env"
            }, status=503)

        data = json.loads(request.body)
        user_message = data.get("message", "")

        try:
            context_data = get_context_data()  

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
                        Eres un asistente especializado en presupuestos y gestión de proyectos de construcción.
                        Usa la siguiente información de la base de datos para responder a las preguntas del usuario:

                        Proyectos: {context_data["proyectos"]}
                        Materiales: {context_data["materiales"]}
                        Trabajadores: {context_data["trabajadores"]}

                        Si el usuario pregunta algo relacionado, utiliza esta información antes de inventar datos.
                        Responde siempre de forma clara y práctica.
                        """
                    },
                    {"role": "user", "content": user_message},
                ],
                max_tokens=300,
            )

            bot_reply = response.choices[0].message.content.strip()
            return JsonResponse({"respuesta": bot_reply})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


def chat_view(request):
    """Renderiza la página del chatbot"""
    return render(request, "chatbot/chat.html")
