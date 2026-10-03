# servicios/ia_service.py

import os
import json
import pandas as pd

from dotenv import load_dotenv
from google import genai


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "No se encontró GEMINI_API_KEY en el archivo .env"
    )


client = genai.Client(
    api_key=API_KEY
)


# ==========================================================
# REGLAS DE LA RUTA
# ==========================================================

RUTA_OFICIAL = [
    "La Cruz",
    "Polo Norte",
    "Iberia",
    "CTM",
    "Iberia",
    "Polo Norte",
    "La Cruz"
]


TIEMPOS_ESPERADOS = {
    "La Cruz -> Polo Norte": 28,
    "Polo Norte -> Iberia": 5,
    "Iberia -> CTM": 13,
    "CTM -> Iberia": 13,
    "Iberia -> Polo Norte": 5,
    "Polo Norte -> La Cruz": 28
}


# ==========================================================
# PREPARAR DATOS PARA GEMINI
# ==========================================================

def preparar_datos_ia(df_resultados):

    if df_resultados is None or df_resultados.empty:

        return []

    datos = []

    for _, fila in df_resultados.iterrows():

        registro = {
            "unidad": str(
                fila.get("Unidad", "")
            ),

            "geocerca": str(
                fila.get("Geocerca", "")
            ),

            "entrada": convertir_fecha(
                fila.get("Entrada", "")
            ),

            "salida": convertir_fecha(
                fila.get("Salida", "")
            ),

            "tiempo_real_minutos": convertir_numero(
                fila.get("TiempoReal")
            ),

            "tiempo_esperado_minutos": convertir_numero(
                fila.get("TiempoEsperado")
            ),

            "diferencia_minutos": convertir_numero(
                fila.get("Diferencia")
            ),

            "estado_python": str(
                fila.get("Estado", "")
            ),

            "tipo": str(
                fila.get("Tipo", "")
            ),

            "anomalia_python": str(
                fila.get("Anomalia", "")
            )
        }

        datos.append(registro)

    return datos


def convertir_numero(valor):

    if valor is None:
        return None

    try:

        if pd.isna(valor):
            return None

        return float(valor)

    except:

        return None


def convertir_fecha(valor):

    if valor is None:
        return ""

    try:

        if pd.isna(valor):
            return ""

    except:
        pass

    if hasattr(valor, "strftime"):

        return valor.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    return str(valor)


# ==========================================================
# CONSTRUIR PROMPT
# ==========================================================

def construir_prompt(datos):

    datos_json = json.dumps(
        datos,
        ensure_ascii=False,
        indent=2
    )

    ruta_texto = " → ".join(
        RUTA_OFICIAL
    )

    tiempos_texto = "\n".join(
        f"- {tramo}: {tiempo} minutos"
        for tramo, tiempo
        in TIEMPOS_ESPERADOS.items()
    )

    prompt = f"""
Eres un analizador de rutas vehiculares.

NO debes inventar reglas.

Debes utilizar EXCLUSIVAMENTE estas reglas:

RUTA OFICIAL:

{ruta_texto}

La ruta se repite continuamente.

Los tiempos esperados son:

{tiempos_texto}

REGLAS:

1. La Cruz → Polo Norte es válido.

2. Polo Norte → Iberia es válido.

3. Iberia → CTM es válido.

4. CTM → Iberia es válido.

5. Iberia → Polo Norte es válido.

6. Polo Norte → La Cruz es válido.

7. Después de La Cruz comienza nuevamente:
   La Cruz → Polo Norte → Iberia → CTM.

8. Si aparece nuevamente la misma geocerca inmediatamente,
   analisar el tiempo entre los duplicados y si son menos de 5 no ha salidos de la geocerca.

9. Un DUPLICADO puede pertecer a la misma deacuerdo al tiempo de salidas de los duplicados.

10. Si se salta una geocerca de la ruta,
    debe marcarse como ANOMALÍA.

11. Nunca debes considerar como válido un tramo directo
    que se haya saltado geocercas.

Ejemplo:

CTM → Polo Norte

NO es un tramo válido.

Debe marcarse:

ANOMALÍA

porque falta:

Iberia

Otro ejemplo:

CTM → La Cruz

NO es válido.

Debe marcarse:

ANOMALÍA

porque faltan:

Iberia
Polo Norte

12. Las geocercas que no sean:

La Cruz
Polo Norte
Iberia
CTM

no deben considerarse para determinar la secuencia de la ruta.

13. Los tiempos deben calcularse usando:

Salida de la geocerca anterior
hasta
Entrada de la geocerca actual.

14. Para un tramo válido se compara:

Tiempo real
contra
Tiempo esperado.

15. Si el tiempo real es menor que el esperado:
   indicar "Más rápido".

16. Si el tiempo real es mayor que el esperado:
   indicar "Más lento".

17. Si son iguales:
   indicar "En tiempo".

18. NO cambies las reglas de Python.

19. NO elimines registros DUPLICADOS.

20. NO inventes tramos.

21. NO corrijas los datos originales.

Tu trabajo es VALIDAR e INTERPRETAR el análisis realizado por Python.

DATOS ANALIZADOS:

{datos_json}

Devuelve tu respuesta exclusivamente en JSON con esta estructura:

{{
    "resumen": "",
    "analisis_correcto": true,
    "unidades_analizadas": 0,
    "tramos_correctos": 0,
    "duplicados": 0,
    "anomalias": 0,
    "observaciones": [],
    "anomalias_detectadas": [],
    "duplicados_detectados": [],
    "recomendaciones": []
}}

IMPORTANTE:

"analisis_correcto" debe indicar si los resultados proporcionados
por Python son coherentes con las reglas oficiales de la ruta.

No debes modificar los resultados.

Si encuentras algo que no coincide, explica exactamente:

- unidad
- geocerca
- secuencia esperada
- secuencia encontrada
- geocerca omitida

No hagas predicciones.
No inventes información que no esté en los datos.
"""

    return prompt


# ==========================================================
# ANALIZAR CON GEMINI
# ==========================================================

def analizar_con_ia(df_resultados):

    if df_resultados is None or df_resultados.empty:

        return {
            "resumen": "No existen resultados para analizar.",
            "analisis_correcto": False,
            "unidades_analizadas": 0,
            "tramos_correctos": 0,
            "duplicados": 0,
            "anomalias": 0,
            "observaciones": [],
            "anomalias_detectadas": [],
            "duplicados_detectados": [],
            "recomendaciones": []
        }

    datos = preparar_datos_ia(
        df_resultados
    )

    prompt = construir_prompt(
        datos
    )

    try:

        respuesta = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        texto = respuesta.text.strip()

        # --------------------------------------------------
        # QUITAR MARKDOWN SI GEMINI LO AGREGA
        # --------------------------------------------------

        if texto.startswith("```json"):

            texto = texto[7:]

        if texto.startswith("```"):

            texto = texto[3:]

        if texto.endswith("```"):

            texto = texto[:-3]

        texto = texto.strip()

        resultado = json.loads(
            texto
        )

        return resultado

    except json.JSONDecodeError:

        return {
            "resumen": (
                "Gemini respondió, pero "
                "la respuesta no tuvo formato JSON válido."
            ),
            "analisis_correcto": False,
            "unidades_analizadas": 0,
            "tramos_correctos": 0,
            "duplicados": 0,
            "anomalias": 0,
            "observaciones": [
                texto
            ],
            "anomalias_detectadas": [],
            "duplicados_detectados": [],
            "recomendaciones": []
        }

    except Exception as e:

        return {
            "resumen": "No fue posible realizar el análisis con IA.",
            "analisis_correcto": False,
            "unidades_analizadas": 0,
            "tramos_correctos": 0,
            "duplicados": 0,
            "anomalias": 0,
            "observaciones": [
                str(e)
            ],
            "anomalias_detectadas": [],
            "duplicados_detectados": [],
            "recomendaciones": []
        }