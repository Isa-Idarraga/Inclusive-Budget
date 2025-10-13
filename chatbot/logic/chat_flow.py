# chatbot/logic/chat_flow.py

from django import forms
from chatbot.utils.chat_utils import generar_pregunta
from chatbot.utils.input_parser import interpretar_respuesta

# 🧠 Estado de conversación temporal (en producción se guarda en sesión o BD)
conversation_state = {}

def iniciar_conversacion(form_class, user_id: str):
    """
    Inicia una nueva conversación con un formulario.
    Retorna la primera pregunta.
    """
    form = form_class()
    fields = list(form.fields.items())
    conversation_state[user_id] = {
        "form": form,
        "current_index": 0,
        "data": {},
    }
    field_name, field = fields[0]
    pregunta = generar_pregunta(field_name, field)
    return pregunta["texto"]

def procesar_respuesta(user_id: str, user_input: str):
    """
    Procesa la respuesta del usuario y devuelve la siguiente pregunta o el resultado final.
    """
    state = conversation_state.get(user_id)
    if not state:
        return "❌ No hay una conversación activa. Escribe 'crear presupuesto' para iniciar una nueva."

    form = state["form"]
    fields = list(form.fields.items())
    index = state["current_index"]

    if index >= len(fields):
        return "✅ Ya completaste todas las preguntas."

    # Campo actual
    field_name, field = fields[index]
    value = interpretar_respuesta(field, user_input)
    state["data"][field_name] = value

    # Pasar al siguiente campo
    index += 1
    state["current_index"] = index

    if index < len(fields):
        next_field_name, next_field = fields[index]
        pregunta = generar_pregunta(next_field_name, next_field)
        return pregunta["texto"]
    else:
        # Validar formulario con los datos obtenidos
        form = form.__class__(data=state["data"])
        if form.is_valid():
            # Si es válido, podríamos guardar el modelo o devolver resumen
            cleaned_data = form.cleaned_data
            del conversation_state[user_id]
            resumen = "\n".join(f"**{k.replace('_', ' ').capitalize()}**: {v}" for k, v in cleaned_data.items())
            return f"🎯 Presupuesto completado correctamente:\n\n{resumen}"
        else:
            errores = "\n".join(f"- {k}: {v}" for k, v in form.errors.items())
            return f"⚠️ Hay errores en el formulario:\n{errores}"
