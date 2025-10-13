# chatbot/utils/input_parser.py
import os
import re
from decimal import Decimal
from openai import OpenAI
# Al principio del archivo:
from django.utils.translation import gettext_lazy as _

client = None
if os.getenv("OPENAI_API_KEY"):
    client = OpenAI()

def interpretar_respuesta(field, user_input: str):
    """Convierte texto humano en un valor compatible con el tipo de campo del formulario."""

    try:
        text = user_input.strip().lower()

        # 🟢 BooleanField (sí/no)
        if field.__class__.__name__ == "BooleanField":
            if any(p in text for p in ["si", "sí", "claro", "obvio", "por supuesto", "afirmativo", "dale"]):
                return True
            if any(p in text for p in ["no", "nunca", "negativo", "para nada"]):
                return False

        # 🟠 ChoiceField
        if hasattr(field, "choices") and field.choices:
            opciones = {str(v).lower(): k for k, v in field.choices}
            for palabra, clave in opciones.items():
                if palabra in text:
                    return clave
            for palabra, clave in opciones.items():
                if any(term in palabra for term in text.split()):
                    return clave

        # 🔵 Números
        if field.__class__.__name__ in ["IntegerField", "DecimalField", "FloatField"]:
            match = re.search(r"(\d+(\.\d+)?)", text)
            if match:
                try:
                    return Decimal(match.group(1))
                except:
                    pass

        # 🟣 Texto libre
        if field.__class__.__name__ in ["CharField", "TextField"]:
            if text in ["no sé", "no lo sé", "ni idea", "ninguno", "n/a"]:
                return ""
            return user_input.strip()

        # Si llegamos aquí, no pudimos interpretar localmente
        if client:
            try:
                tipo = field.__class__.__name__
                instrucciones = f"""
                Interpreta esta respuesta humana para un campo tipo {tipo}.
                Devuelve solo el valor más apropiado, sin explicación.
                Si no se puede determinar, devuelve 'None'.
                Respuesta: {user_input}
                Opciones (si existen): {getattr(field, 'choices', None)}
                """
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Eres un asistente que interpreta entradas humanas para formularios."},
                        {"role": "user", "content": instrucciones}
                    ],
                    temperature=0.2,
                    max_tokens=40
                )
                value = response.choices[0].message.content.strip()
                if value.lower() in ["none", "null", "desconocido"]:
                    return None
                return value
            except Exception as e:
                print("⚠️ Error interpretando con IA:", e)
    except Exception as e:
        print("⚠️ Error interpretando respuesta:", e)
    # Último recurso → devolver texto crudo
        return user_input.strip()
