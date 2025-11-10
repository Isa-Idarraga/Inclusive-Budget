# chatbot/services/budget_estimator.py
import os
import json
from openai import OpenAI


class BudgetEstimator:
    """
    Estimador híbrido de presupuestos: combina cálculo base + refinamiento IA
    Basado en el código original de estimación
    """
    
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
- Garajes: +8.000.000 - 15.000.000 COP por plaza (incluye excavación, estructura, acabados)
- Zonas verdes: +80.000 - 150.000 COP/m² (incluye césped, plantas, riego, adoquín)
- Si hay muchos "no sé": reduce confidence 20–40 pts.

Tu entrada incluirá un valor base calculado en COP y los detalles del proyecto.
Refina ese valor base aplicando tus conocimientos técnicos, de mercado y contexto local.

IMPORTANTE: Considera explícitamente el número de garajes y área de zonas verdes en tu estimación.
"""
    
    def __init__(self, api_key=None, model=None):
        self.client = None
        if api_key or os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def estimate(self, datos_dict: dict) -> dict:
        """
        Estima el presupuesto combinando cálculo base + refinamiento IA
        
        Args:
            datos_dict: Diccionario con datos del proyecto
            
        Returns:
            dict con estimación completa
        """
        # Calcular base
        base = self._calcular_estimacion_base(datos_dict)
        
        # Si no hay área, devolver cero
        if base["total_estimado"] == 0:
            return {
                "total_estimated_cop": 0,
                "cost_per_m2_cop": 0,
                "breakdown": [],
                "rationale": "Datos insuficientes (falta área construida).",
                "confidence": 0
            }
        
        # Si no hay cliente IA, devolver solo el cálculo base
        if not self.client:
            return {
                "total_estimated_cop": base["total_estimado"],
                "cost_per_m2_cop": base["costo_m2_ajustado"],
                "breakdown": [
                    {
                        "factor": "Cálculo base local",
                        "impact_pct": 0,
                        "impact_cop": base["total_estimado"]
                    }
                ],
                "rationale": "Estimación basada en cálculo local (sin refinamiento IA).",
                "confidence": 70
            }
        
        # Refinar con IA
        return self._refinar_con_ia(base, datos_dict)
    
    def _calcular_estimacion_base(self, datos: dict) -> dict:
        """Calcula una estimación básica por fórmula antes de IA"""
        try:
            area = float(datos.get("area_construida_total", 0))
        except:
            area = 0
        
        acabado = str(datos.get("acabado_muros", "")).lower()
        ubicacion = str(datos.get("ubicacion_proyecto", "")).lower()
        pisos = int(datos.get("numero_pisos", 1) or 1)
        terreno = str(datos.get("tipo_terreno", "")).lower()
        acceso = str(datos.get("acceso_obra", "")).lower()
        
        # 🆕 Extraer garajes y zonas verdes
        try:
            plazas_garaje = int(datos.get("plazas_garaje", 0))
        except:
            plazas_garaje = 0
        
        try:
            area_zonas_verdes = float(datos.get("area_zonas_verdes", 0))
        except:
            area_zonas_verdes = 0
        
        # Valor base por m²
        if "premium" in acabado or "alto" in acabado:
            base_m2 = 3500000
        elif "estandar" in acabado or "estándar" in acabado or "medio" in acabado:
            base_m2 = 2700000
        else:
            base_m2 = 1900000
        
        # Ajustes
        factor = 1.0
        
        # Ubicación
        if "bogotá" in ubicacion or "bogota" in ubicacion:
            factor += 0.20
        elif "medellín" in ubicacion or "medellin" in ubicacion:
            factor += 0.10
        elif "cali" in ubicacion:
            factor += 0.05
        
        # Acceso
        if "difícil" in acceso or "dificil" in acceso or "complicado" in acceso:
            factor += 0.15
        elif "medio" in acceso or "regular" in acceso:
            factor += 0.07
        
        # Terreno
        if "blando" in terreno or "relleno" in terreno:
            factor += 0.10
        elif "pendiente" in terreno or "inclinado" in terreno:
            factor += 0.12
        
        # Pisos adicionales
        if pisos > 1:
            factor += 0.05 * (pisos - 1)
        
        # 🆕 AGREGAR AJUSTES PREMIUM ESPECÍFICOS
        piso_social = str(datos.get("piso_zona_social", "")).lower()
        instalaciones = str(datos.get("instalaciones_especiales", "")).lower()
        ventanas = str(datos.get("porcentaje_ventanas", "")).lower()
        puerta = str(datos.get("puerta_principal_especial", "")).lower()
        
        # Mármol/granito: +15% adicional
        if "marmol" in piso_social or "mármol" in piso_social or "granito" in piso_social:
            factor += 0.15
        
        # Sistema de riego: +5%
        if "riego" in instalaciones:
            factor += 0.05
        
        # Alto porcentaje ventanas: +8%
        if "alto" in ventanas:
            factor += 0.08
        
        # Puerta blindada: +3%
        if "blindada" in puerta:
            factor += 0.03
        
        costo_m2_ajustado = int(base_m2 * factor)
        total = int(area * costo_m2_ajustado)
        
        # 🆕 AGREGAR COSTOS DE GARAJES
        # Costo promedio por plaza: 12.000.000 COP
        costo_garajes = plazas_garaje * 12000000
        
        # 🆕 AGREGAR COSTOS DE ZONAS VERDES
        # Costo promedio: 120.000 COP/m² (incluye césped, plantas, riego)
        costo_zonas_verdes = int(area_zonas_verdes * 120000)
        
        # Total con garajes y zonas verdes
        total_final = total + costo_garajes + costo_zonas_verdes
        
        return {
            "base_costo_m2": base_m2,
            "ajuste_factor": round(factor, 2),
            "costo_m2_ajustado": costo_m2_ajustado,
            "total_estimado": total_final,
            "costo_construccion_base": total,
            "costo_garajes": costo_garajes,
            "plazas_garaje": plazas_garaje,
            "costo_zonas_verdes": costo_zonas_verdes,
            "area_zonas_verdes": area_zonas_verdes,
        }
    
    def _refinar_con_ia(self, base: dict, datos_dict: dict) -> dict:
        """Refina la estimación usando IA"""
        
        # Construir entrada para la IA
        resumen = "\n".join(f"{k}: {v}" for k, v in datos_dict.items())
        
        # 🆕 Agregar información explícita sobre garajes y zonas verdes
        detalles_adicionales = f"""
Detalles adicionales calculados:
- Plazas de garaje: {base.get('plazas_garaje', 0)} (costo base: ${base.get('costo_garajes', 0):,} COP)
- Zonas verdes: {base.get('area_zonas_verdes', 0)} m² (costo base: ${base.get('costo_zonas_verdes', 0):,} COP)
- Costo construcción base (sin garajes/zonas): ${base.get('costo_construccion_base', 0):,} COP
"""
        
        entrada = (
            f"{self.BASE_PROMPT}\n\n"
            f"Valor base de cálculo (antes de IA): {base['total_estimado']} COP "
            f"({base['costo_m2_ajustado']} COP/m²)\n\n"
            f"{detalles_adicionales}\n"
            f"Datos del proyecto:\n{resumen}"
        )
        
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": entrada}],
                temperature=0.25,
                max_tokens=600  # Aumentado para incluir más detalles
            )
            text = resp.choices[0].message.content.strip()
            
            # Intentar extraer JSON
            result = self._extract_json(text)
            
            if not result or "total_estimated_cop" not in result:
                return self._fallback_response(base, "Error en respuesta de IA")
            
            # Integrar datos de IA + base
            result["base_total_estimate"] = base["total_estimado"]
            result["base_cost_per_m2"] = base["costo_m2_ajustado"]
            result["garages_cost"] = base.get("costo_garajes", 0)
            result["green_areas_cost"] = base.get("costo_zonas_verdes", 0)
            result["ai_adjustment_pct"] = round(
                (result["total_estimated_cop"] - base["total_estimado"]) / base["total_estimado"] * 100, 2
            ) if base["total_estimado"] > 0 else 0
            
            return result
            
        except Exception as e:
            return self._fallback_response(base, f"Error al contactar IA: {str(e)}")
    
    def _extract_json(self, text: str) -> dict:
        """Extrae JSON del texto de respuesta"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Intentar encontrar JSON en el texto
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
        return None
    
    def _fallback_response(self, base: dict, reason: str) -> dict:
        """Respuesta de fallback cuando falla la IA"""
        breakdown = [
            {
                "factor": "Construcción base",
                "impact_pct": 0,
                "impact_cop": base.get("costo_construccion_base", base["total_estimado"])
            }
        ]
        
        # Agregar garajes si existen
        if base.get("costo_garajes", 0) > 0:
            breakdown.append({
                "factor": f"Garajes ({base.get('plazas_garaje', 0)} plazas)",
                "impact_pct": round((base["costo_garajes"] / base["total_estimado"]) * 100, 1),
                "impact_cop": base["costo_garajes"]
            })
        
        # Agregar zonas verdes si existen
        if base.get("costo_zonas_verdes", 0) > 0:
            breakdown.append({
                "factor": f"Zonas verdes ({base.get('area_zonas_verdes', 0)} m²)",
                "impact_pct": round((base["costo_zonas_verdes"] / base["total_estimado"]) * 100, 1),
                "impact_cop": base["costo_zonas_verdes"]
            })
        
        return {
            "total_estimated_cop": base["total_estimado"],
            "cost_per_m2_cop": base["costo_m2_ajustado"],
            "breakdown": breakdown,
            "rationale": f"Se devolvió la estimación base. {reason}",
            "confidence": 60
        }


# Función de conveniencia para uso directo
def estimar_presupuesto_ia(datos_dict: dict) -> dict:
    """
    Función wrapper para mantener compatibilidad con código existente
    """
    estimator = BudgetEstimator()
    return estimator.estimate(datos_dict)