import os, json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === PROMPT PRINCIPAL ===
BASE_PROMPT = """
Eres un ingeniero civil y estimador de costos con experiencia en Colombia (2024–2025).
Tu tarea: con los datos del proyecto que te doy, producir una estimación refinada del costo total
de construcción (en pesos colombianos, COP), validando y ajustando un valor base que ya te entrego.

>>> Reglas formales:
1. Devuelve SOLO un objeto JSON válido (sin texto adicional) con estas claves:
   - total_estimated_cop: entero (sin separadores)
   - cost_per_m2_cop: entero
   - breakdown: lista de objetos { "factor": str, "impact_pct": número, "impact_cop": entero }
   - rationale: string corta (1–3 oraciones)
   - confidence: número 0-100
2. Usa COP. Números redondeados.
3. Si los datos están incompletos, reduce confidence.
4. Considera contexto colombiano, precios 2025 y ajustes regionales.

>>> Rangos de referencia (COP/m², 2025):
- Básico: 1.300.000 – 2.300.000
- Estándar: 2.300.000 – 3.200.000
- Premium: 2.900.000 – 4.000.000+

Factores típicos:
- Terreno difícil / acceso complicado: +10–25%
- Acabados premium / dotación eléctrica alta: +10–30%
- Pisos adicionales: +5–15% por nivel extra
- Licencias / estudios: +3–8%
- Ubicación (Bogotá/Medellín/Cali): +5–25%
- Si hay muchos “no sé”: reduce confidence 20–40 pts.

Tu entrada incluirá un valor base calculado en COP y los detalles del proyecto.
Refina ese valor base aplicando tus conocimientos técnicos, de mercado y contexto local.
"""

# === FUNCIÓN DE CÁLCULO BASE (fórmula Python) ===
def calcular_estimacion_base(datos):
    """Calcula una estimación básica por fórmula antes de IA."""
    try:
        area = float(datos.get("area_construida_total", 0))
    except:
        area = 0

    acabado = str(datos.get("acabado_muros", "")).lower()
    ubicacion = str(datos.get("ubicacion_proyecto", "")).lower()
    pisos = int(datos.get("numero_pisos", 1) or 1)
    terreno = str(datos.get("tipo_terreno", "")).lower()
    acceso = str(datos.get("acceso_obra", "")).lower()

    # Valor base por m²
    if "premium" in acabado:
        base_m2 = 3500000
    elif "estandar" in acabado or "medio" in acabado:
        base_m2 = 2700000
    else:
        base_m2 = 1900000

    # Ajustes
    factor = 1.0
    if "bogotá" in ubicacion or "bogota" in ubicacion:
        factor += 0.20
    elif "medellín" in ubicacion or "medellin" in ubicacion:
        factor += 0.10
    elif "cali" in ubicacion:
        factor += 0.05

    if "difícil" in acceso or "dificil" in acceso:
        factor += 0.15
    elif "medio" in acceso:
        factor += 0.07

    if "blando" in terreno or "relleno" in terreno:
        factor += 0.10

    if pisos > 1:
        factor += 0.05 * (pisos - 1)

    costo_m2_ajustado = int(base_m2 * factor)
    total = int(area * costo_m2_ajustado)

    return {
        "base_costo_m2": base_m2,
        "ajuste_factor": round(factor, 2),
        "costo_m2_ajustado": costo_m2_ajustado,
        "total_estimado": total
    }

# === FUNCIÓN PRINCIPAL (IA + fórmula híbrida) ===
def estimar_presupuesto_ia(datos_dict: dict) -> dict:
    """
    Combina una estimación base matemática con refinamiento por IA.
    """
    base = calcular_estimacion_base(datos_dict)

    # Si no hay área, devolver cero directamente
    if base["total_estimado"] == 0:
        return {
            "total_estimated_cop": 0,
            "cost_per_m2_cop": 0,
            "breakdown": [],
            "rationale": "Datos insuficientes (falta área construida).",
            "confidence": 0
        }

    # Construir entrada para la IA
    resumen = "\n".join(f"{k}: {v}" for k, v in datos_dict.items())
    entrada = (
        f"{BASE_PROMPT}\n\n"
        f"Valor base de cálculo (antes de IA): {base['total_estimado']} COP "
        f"({base['costo_m2_ajustado']} COP/m²)\n\n"
        f"Datos del proyecto:\n{resumen}"
    )

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": entrada}],
            temperature=0.25,
            max_tokens=500
        )
        text = resp.choices[0].message.content.strip()

        # Intentar extraer JSON
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1:
                result = json.loads(text[start:end+1])
            else:
                result = None

        if not result or "total_estimated_cop" not in result:
            # Fallback si IA no responde correctamente
            return {
                "total_estimated_cop": base["total_estimado"],
                "cost_per_m2_cop": base["costo_m2_ajustado"],
                "breakdown": [
                    {"factor": "Cálculo base local", "impact_pct": 0, "impact_cop": base["total_estimado"]}
                ],
                "rationale": "Se devolvió la estimación base debido a error en la respuesta de IA.",
                "confidence": 60
            }

        # Integrar datos de IA + base
        result["base_total_estimate"] = base["total_estimado"]
        result["base_cost_per_m2"] = base["costo_m2_ajustado"]
        result["ai_adjustment_pct"] = round(
            (result["total_estimated_cop"] - base["total_estimado"]) / base["total_estimado"] * 100, 2
        )
        return result

    except Exception as e:
        # Fallback total
        return {
            "total_estimated_cop": base["total_estimado"],
            "cost_per_m2_cop": base["costo_m2_ajustado"],
            "breakdown": [
                {"factor": "Cálculo base local", "impact_pct": 0, "impact_cop": base["total_estimado"]}
            ],
            "rationale": f"Error al contactar IA: {str(e)}",
            "confidence": 50
        }
