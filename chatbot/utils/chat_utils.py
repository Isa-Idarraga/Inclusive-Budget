# chatbot/utils/chat_utils.py
def generar_pregunta(field_name, field):
    """Genera una pregunta más natural y lista de opciones, si aplica."""
    label = field.label or field_name.replace("_", " ").capitalize()

    # Base genérica
    pregunta = f"Por favor ingresa el valor para **{label}**:"
    opciones = []

    # Si el campo tiene choices, genera la lista de opciones
    if hasattr(field, "choices") and field.choices:
        opciones = [label for _, label in field.choices]
        pregunta = f"📋 ¿Cuál de las siguientes opciones describe mejor **{label}**?\n"
        pregunta += "\n".join(f"- {opt}" for opt in opciones)

    # Personaliza casos comunes
    if "sí" in label.lower() or "requiere" in label.lower():
        pregunta = f"{label} (responde 'sí' o 'no'):"

    return {"texto": pregunta, "opciones": opciones}
