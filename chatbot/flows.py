# chatbot/assistants/budget_assistant.py

from decimal import Decimal
from projects.forms import ProjectForm
from projects.models import Material
from chatbot.utils.chat_utils import generar_pregunta
from chatbot.utils.input_parser import interpretar_respuesta
from chatbot.utils.ai_cost_estimator import estimar_presupuesto_ia


class BudgetAssistant:
    """
    Asistente paso a paso para crear un proyecto con presupuesto.
    Controla el estado de la conversación en sesión y maneja errores de entrada.
    """

    def __init__(self, session_state: dict):
        self.session = session_state or {}
        self.form = ProjectForm()
        self.fields = list(self.form.fields.keys())
        self.current_index = self.session.get("current_index", 0)
        self.data = self.session.get("data", {})
        self.is_finished = self.session.get("is_finished", False)

    # -------------------------------------------------------------------------
    # 🔹 Lógica principal del flujo
    # -------------------------------------------------------------------------
    def process_answer(self, user_input: str) -> str:
        user_input = user_input.strip()

        # 🚫 Cancelar proceso
        if user_input.lower() in ["cancelar", "parar", "salir", "detener"]:
            self.session.clear()
            self.is_finished = True
            return "✅ Proceso cancelado. No se guardaron datos."

        # 💾 Confirmar y guardar
        if user_input.lower() in ["sí", "si", "guardar", "confirmar", "crear proyecto"]:
            return self.save_project()

        # ⚠️ Ya terminó
        if self.current_index >= len(self.fields):
            return "⚠️ Ya me diste toda la información. Escribe 'sí' para confirmar o 'cancelar' para abortar."

        # 🧠 Interpretar respuesta
        field_name = self.fields[self.current_index]
        field = self.form.fields[field_name]
        valor_interpretado = interpretar_respuesta(field, user_input)

        # Guardar valor
        self.data[field_name] = valor_interpretado if valor_interpretado is not None else user_input
        self.current_index += 1

        # Actualizar sesión
        self.session.update({
            "data": self.data,
            "current_index": self.current_index,
            "is_finished": False,
        })

        # Si completó todo → calcular presupuesto
        if self.current_index == len(self.fields):
            return self.calculate_estimate()

        # Continuar con siguiente pregunta
        return self.next_question()

    # -------------------------------------------------------------------------
    # 🔹 Preguntar siguiente campo
    # -------------------------------------------------------------------------
    def next_question(self) -> str:
        if self.current_index < len(self.fields):
            field_name = self.fields[self.current_index]
            field = self.form.fields[field_name]

            pregunta_data = generar_pregunta(field_name, field)
            self.session["current_options"] = pregunta_data.get("opciones", [])
            self.session["current_question"] = field_name

            texto = pregunta_data["texto"]

            # Agregar opciones si hay
            if pregunta_data["opciones"]:
                texto += "\n\nResponde con una de las opciones o escribe tu respuesta."

            return texto

        return "✅ Ya tengo toda la información. Escribe 'sí' para guardar el proyecto o 'cancelar' para salir."

    # -------------------------------------------------------------------------
    # 🔹 Calcular presupuesto estimado (IA + materiales)
    # -------------------------------------------------------------------------
    def calculate_estimate(self) -> str:
        try:
            # 🧾 Cálculo base con materiales
            total = Decimal("0.00")
            for material in Material.objects.all():
                total += Decimal(material.unit_cost or 0)

            total = round(total, 2)
            self.session["estimated_total"] = str(total)

            # 🧠 Estimación con IA
            try:
                resumen_datos = "\n".join([f"{k}: {v}" for k, v in self.data.items()])
                estimacion_ia = estimar_presupuesto_ia(resumen_datos)
            except Exception as e:
                estimacion_ia = f"No disponible (error IA: {str(e)})"

            return (
                f"💰 Cálculo base del presupuesto: **{total} COP**\n\n"
                f"🤖 Estimación inteligente de la IA:\n{estimacion_ia}\n\n"
                "¿Deseas crear el proyecto con estos datos? (responde 'sí' o 'cancelar')"
            )

        except Exception as e:
            return f"⚠️ No pude calcular el presupuesto automáticamente ({str(e)}). Escribe 'sí' para guardar o 'cancelar' para abortar."

    # -------------------------------------------------------------------------
    # 🔹 Guardar proyecto
    # -------------------------------------------------------------------------
    def save_project(self) -> str:
        try:
            form = ProjectForm(self.data)

            if form.is_valid():
                project = form.save()
                self.session.clear()
                self.is_finished = True
                return f"✅ Proyecto **{project.name}** creado correctamente en la base de datos."

            # ❌ Errores del formulario
            error_msgs = "; ".join(
                [f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()]
            )
            return f"❌ No se pudo crear el proyecto. Revisa los datos ingresados.\nDetalles: {error_msgs}"

        except Exception as e:
            return f"⚠️ Error inesperado al guardar el proyecto: {str(e)}"
