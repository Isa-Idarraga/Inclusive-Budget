import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from groq import Groq  
from .services import get_context_data  

# Cliente Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

@csrf_exempt
def chat_api(request):
    """API que recibe mensajes del frontend y responde con Groq"""
    if request.method == "POST":
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
