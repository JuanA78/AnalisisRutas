# servicios/analisis_service.py

import pandas as pd

from servicios.ruta_service import (
    RUTA_COMPLETA,
    obtener_tiempo_esperado,
    es_geocerca_de_ruta
)


# ==========================================================
# UTILIDADES
# ==========================================================

def calcular_minutos(fecha_inicio, fecha_fin):

    if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
        return None

    diferencia = fecha_fin - fecha_inicio

    return diferencia.total_seconds() / 60


def formatear_minutos(minutos):

    if minutos is None or pd.isna(minutos):
        return ""

    segundos = int(round(float(minutos) * 60))

    horas = segundos // 3600
    segundos %= 3600

    minutos_enteros = segundos // 60
    segundos_restantes = segundos % 60

    if horas > 0:
        return f"{horas:02d}:{minutos_enteros:02d}:{segundos_restantes:02d}"

    return f"{minutos_enteros:02d}:{segundos_restantes:02d}"


def diferencia_minutos(tiempo_real, tiempo_esperado):

    if tiempo_real is None or tiempo_esperado is None:
        return None

    return tiempo_real - tiempo_esperado


# ==========================================================
# POSICIONES DE LA RUTA
# ==========================================================

def obtener_siguiente_posicion(posicion_actual):

    """
    Regresa la siguiente posición esperada.

    Ejemplo:

    La Cruz       posición 0
    Polo Norte    posición 1
    Iberia        posición 2
    CTM           posición 3
    Iberia        posición 4
    Polo Norte    posición 5
    La Cruz       posición 6
    """

    if posicion_actual is None:
        return 0

    siguiente = posicion_actual + 1

    if siguiente >= len(RUTA_COMPLETA):
        # Después de regresar a La Cruz
        # empieza otra ida
        return 1

    return siguiente


def posiciones_geocerca(geocerca):

    """
    Devuelve todas las posiciones donde aparece
    una geocerca dentro de la ruta.

    Ejemplo:

    Iberia -> [2, 4]
    Polo Norte -> [1, 5]
    La Cruz -> [0, 6]
    """

    return [
        indice
        for indice, valor in enumerate(RUTA_COMPLETA)
        if valor == geocerca
    ]


def buscar_siguiente_posicion_valida(
    geocerca,
    posicion_actual
):

    """
    Busca dónde aparece la geocerca actual después
    de la posición actual.

    Sirve para detectar geocercas omitidas.
    """

    posiciones = posiciones_geocerca(geocerca)

    if not posiciones:
        return None

    for posicion in posiciones:

        if posicion > posicion_actual:
            return posicion

    # Si no existe después, puede ser el inicio
    # de una nueva vuelta.
    for posicion in posiciones:

        if posicion == 0:
            return posicion

    return None


def obtener_geocercas_omitidas(
    posicion_actual,
    posicion_encontrada
):

    """
    Regresa las geocercas que debieron aparecer
    entre dos posiciones.
    """

    if posicion_encontrada is None:
        return []

    if posicion_encontrada <= posicion_actual:
        return []

    return RUTA_COMPLETA[
        posicion_actual + 1:posicion_encontrada
    ]


# ==========================================================
# ANALIZAR UNA UNIDAD
# ==========================================================

def analizar_unidad(df_unidad):

    if df_unidad is None or df_unidad.empty:

        return pd.DataFrame()

    datos = df_unidad.copy()

    # ------------------------------------------------------
    # ORDEN CRONOLÓGICO
    # ------------------------------------------------------

    datos = datos.sort_values(
        by="FechaHoraEntrada"
    ).reset_index(drop=True)

    resultados = []

    # ------------------------------------------------------
    # ESTADO DE LA RUTA
    # ------------------------------------------------------

    posicion_ruta = None

    evento_anterior = None

    # ======================================================
    # RECORRER REGISTROS
    # ======================================================

    for _, evento in datos.iterrows():

        geocerca = str(
            evento["Geocerca"]
        ).strip()

        # --------------------------------------------------
        # IGNORAR GEOCERCAS QUE NO PERTENECEN A LA RUTA
        # --------------------------------------------------

        if not es_geocerca_de_ruta(geocerca):

            continue

        entrada_actual = evento["FechaHoraEntrada"]
        salida_actual = evento["FechaHoraSalida"]

        # ==================================================
        # PRIMERA GEOCERCA
        # ==================================================

        if evento_anterior is None:

            # La ruta debe comenzar en La Cruz

            if geocerca == "La Cruz":

                posicion_ruta = 0

                resultados.append(
                    crear_resultado(
                        evento=evento,
                        geocerca=geocerca,
                        estado="Inicio",
                        tipo="Inicio de ruta",
                        anomalia=""
                    )
                )

                evento_anterior = evento

                continue

            else:

                # Antes de encontrar La Cruz,
                # todavía no iniciamos el análisis.

                continue

        # ==================================================
        # DUPLICADO
        # ==================================================

        geocerca_anterior = str(
            evento_anterior["Geocerca"]
        ).strip()

        if geocerca == geocerca_anterior:

            resultados.append(
                crear_resultado(
                    evento=evento,
                    geocerca=geocerca,
                    estado="Duplicado",
                    tipo="Registro duplicado",
                    anomalia=(
                        f"Registro repetido de {geocerca}"
                    ),
                    evento_anterior=evento_anterior
                )
            )

            # MUY IMPORTANTE:
            #
            # No cambiamos posicion_ruta.
            #
            # El duplicado NO avanza la ruta.

            evento_anterior = evento

            continue

        # ==================================================
        # SIGUIENTE GEOCERCA ESPERADA
        # ==================================================

        siguiente_posicion = obtener_siguiente_posicion(
            posicion_ruta
        )

        geocerca_esperada = RUTA_COMPLETA[
            siguiente_posicion
        ]

        # ==================================================
        # CASO CORRECTO
        # ==================================================

        if geocerca == geocerca_esperada:

            resultados.append(
                crear_resultado(
                    evento=evento,
                    geocerca=geocerca,
                    estado="Correcto",
                    tipo="Tramo válido",
                    anomalia="",
                    evento_anterior=evento_anterior
                )
            )

            posicion_ruta = siguiente_posicion

            evento_anterior = evento

            continue

        # ==================================================
        # ANOMALÍA
        # ==================================================

        posicion_encontrada = buscar_siguiente_posicion_valida(
            geocerca,
            posicion_ruta
        )

        geocercas_omitidas = obtener_geocercas_omitidas(
            posicion_ruta,
            posicion_encontrada
        )

        # --------------------------------------------------
        # CREAR TEXTO DE ANOMALÍA
        # --------------------------------------------------

        if geocercas_omitidas:

            texto_omitidas = ", ".join(
                geocercas_omitidas
            )

            anomalia = (
                f"Se omitió: {texto_omitidas}"
            )

        else:

            anomalia = (
                f"Secuencia inesperada: "
                f"se esperaba {geocerca_esperada}"
            )

        resultados.append(
            crear_resultado(
                evento=evento,
                geocerca=geocerca,
                estado="Anomalía",
                tipo="Tramo anómalo",
                anomalia=anomalia,
                evento_anterior=evento_anterior
            )
        )

        # --------------------------------------------------
        # SINCRONIZAMOS LA RUTA
        #
        # Esto es importante.
        #
        # Si ocurrió:
        #
        # CTM → Polo Norte
        #
        # y faltó Iberia,
        #
        # ahora Polo Norte pasa a ser la posición actual.
        # --------------------------------------------------

        if posicion_encontrada is not None:

            posicion_ruta = posicion_encontrada

        else:

            # Si no podemos encontrar la posición,
            # reiniciamos esperando una nueva La Cruz.

            posicion_ruta = None

        evento_anterior = evento

    # ======================================================
    # DATAFRAME FINAL
    # ======================================================

    if not resultados:

        return pd.DataFrame()

    resultado = pd.DataFrame(resultados)

    return resultado


# ==========================================================
# CREAR RESULTADO
# ==========================================================

def crear_resultado(
    evento,
    geocerca,
    estado,
    tipo,
    anomalia,
    evento_anterior=None
):

    unidad = evento["Unidad"]

    entrada = evento["FechaHoraEntrada"]

    salida = evento["FechaHoraSalida"]

    tiempo_real = None
    tiempo_esperado = None
    diferencia = None

    # ------------------------------------------------------
    # CALCULAR TIEMPOS
    # ------------------------------------------------------

    if evento_anterior is not None:

        salida_anterior = (
            evento_anterior["FechaHoraSalida"]
        )

        geocerca_anterior = str(
            evento_anterior["Geocerca"]
        ).strip()

        tiempo_real = calcular_minutos(
            salida_anterior,
            entrada
        )

        # --------------------------------------------------
        # SOLO calculamos tiempo esperado si el tramo
        # realmente existe en la ruta.
        # --------------------------------------------------

        tiempo_esperado = obtener_tiempo_esperado(
            geocerca_anterior,
            geocerca
        )

        diferencia = diferencia_minutos(
            tiempo_real,
            tiempo_esperado
        )

    # ------------------------------------------------------
    # ESTADO DEL TIEMPO
    # ------------------------------------------------------

    if (
        estado == "Correcto"
        and tiempo_real is not None
        and tiempo_esperado is not None
    ):

        if diferencia > 0:

            estado_tiempo = "Más lento"

        elif diferencia < 0:

            estado_tiempo = "Más rápido"

        else:

            estado_tiempo = "En tiempo"

    else:

        estado_tiempo = ""

    return {
        "Unidad": unidad,

        "Geocerca": geocerca,

        "Entrada": entrada,

        "Salida": salida,

        "TiempoReal": tiempo_real,

        "TiempoEsperado": tiempo_esperado,

        "Diferencia": diferencia,

        "Estado": estado,

        "Tipo": tipo,

        "Anomalia": anomalia,

        "EstadoTiempo": estado_tiempo
    }


# ==========================================================
# ANALIZAR VARIAS UNIDADES
# ==========================================================

def analizar_unidades(df, unidades):

    if df is None or df.empty:

        return pd.DataFrame()

    if not unidades:

        return pd.DataFrame()

    resultados = []

    for unidad in unidades:

        datos_unidad = df[
            df["Unidad"].astype(str).str.strip()
            == str(unidad).strip()
        ].copy()

        if datos_unidad.empty:

            continue

        resultado_unidad = analizar_unidad(
            datos_unidad
        )

        if not resultado_unidad.empty:

            resultados.append(
                resultado_unidad
            )

    if not resultados:

        return pd.DataFrame()

    resultado_final = pd.concat(
        resultados,
        ignore_index=True
    )

    return resultado_final


# ==========================================================
# RESUMEN PARA EL DASHBOARD
# ==========================================================

def obtener_resumen(df_resultados):

    if (
        df_resultados is None
        or df_resultados.empty
    ):

        return {
            "unidades": 0,
            "total_tramos": 0,
            "mas_rapidos": 0,
            "mas_lentos": 0,
            "tiempo_promedio": 0,
            "anomalias": 0,
            "duplicados": 0
        }

    unidades = (
        df_resultados["Unidad"]
        .nunique()
    )

    total_tramos = (
        df_resultados["Tipo"]
        == "Tramo válido"
    ).sum()

    mas_rapidos = (
        df_resultados["EstadoTiempo"]
        == "Más rápido"
    ).sum()

    mas_lentos = (
        df_resultados["EstadoTiempo"]
        == "Más lento"
    ).sum()

    anomalias = (
        df_resultados["Estado"]
        == "Anomalía"
    ).sum()

    duplicados = (
        df_resultados["Estado"]
        == "Duplicado"
    ).sum()

    tiempos = pd.to_numeric(
        df_resultados[
            "TiempoReal"
        ],
        errors="coerce"
    ).dropna()

    if tiempos.empty:

        tiempo_promedio = 0

    else:

        tiempo_promedio = float(
            tiempos.mean()
        )

    return {
        "unidades": int(unidades),

        "total_tramos": int(total_tramos),

        "mas_rapidos": int(mas_rapidos),

        "mas_lentos": int(mas_lentos),

        "tiempo_promedio": tiempo_promedio,

        "anomalias": int(anomalias),

        "duplicados": int(duplicados)
    }