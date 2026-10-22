import warnings
import pandas as pd
from configuracion.rutas_config import RutasConfig

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class RutaService:
    """
    Servicio encargado de procesar y analizar los recorridos de las unidades.
    Identifica vueltas, cortes, geocercas omitidas, desvíos de ruta, evalúa tiempos
    y calcula estadísticas acumuladas de retrasos.
    """

    # =========================================================================
    # SECCIÓN A: UTILIDADES Y ESTRUCTURA BASE
    # =========================================================================

    @staticmethod
    def _formatear_min_seg(segundos: float) -> str:
        """Convierte segundos a formato 'Xm YYs'."""
        if pd.isna(segundos) or segundos < 0:
            return "-"
        tot_seg = int(round(segundos))
        minutos = tot_seg // 60
        segs = tot_seg % 60
        return f"{minutos}m {segs:02d}s"

    @staticmethod
    def es_reporte_semanal(df_unidades: pd.DataFrame) -> bool:
        """Determina si el reporte abarca múltiples días."""
        if df_unidades is None or df_unidades.empty:
            return False

        cols = [
            c for c in df_unidades.columns
            if any(k in str(c).lower() for k in ["tiempo total", "duración", "duracion"])
        ]
        if not cols:
            return False

        for col in cols:
            valores_str = df_unidades[col].astype(str).str.lower()
            if valores_str.str.contains("día|días|dia|dias").any():
                return True

        return False

    @staticmethod
    def _obtener_secuencias_por_ruta(nombre_ruta: str) -> list:
        """Devuelve únicamente las secuencias oficiales de la ruta seleccionada."""
        if str(nombre_ruta).strip().lower() == "agua salada":
            return RutasConfig.SECUENCIAS_AGUA_SALADA
        return RutasConfig.SECUENCIAS_EL_ARBOLITO

    @classmethod
    def _obtener_secuencia_intermedia(
        cls, origen: str, destino: str, nombre_ruta: str = "El Arbolito"
    ) -> list:
        """Obtiene las geocercas intermedias exclusivamente dentro de la ruta activa."""
        secuencias = cls._obtener_secuencias_por_ruta(nombre_ruta)

        for secuencia in secuencias:
            if origen in secuencia and destino in secuencia:
                idx_orig = secuencia.index(origen)
                idx_dest = secuencia.index(destino)

                if idx_dest > idx_orig + 1:
                    return secuencia[idx_orig + 1 : idx_dest]

        return []

    @classmethod
    def _calcular_meta_acumulada(
        cls, origen: str, destino: str, tiempos_objetivo: dict, nombre_ruta: str = "El Arbolito"
    ) -> float:
        """Calcula el tiempo objetivo directo o acumulado usando solo las secuencias de la ruta activa."""
        if not tiempos_objetivo:
            return 0.0

        if (origen, destino) in tiempos_objetivo:
            return float(tiempos_objetivo[(origen, destino)])

        secuencias = cls._obtener_secuencias_por_ruta(nombre_ruta)

        for secuencia in secuencias:
            if origen in secuencia and destino in secuencia:
                idx_orig = secuencia.index(origen)
                idx_dest = secuencia.index(destino)

                if idx_dest > idx_orig:
                    sub_secuencia = secuencia[idx_orig : idx_dest + 1]
                    meta_total = 0.0
                    valido = True

                    for i in range(len(sub_secuencia) - 1):
                        p1, p2 = sub_secuencia[i], sub_secuencia[i + 1]
                        if (p1, p2) in tiempos_objetivo:
                            meta_total += float(tiempos_objetivo[(p1, p2)])
                        else:
                            valido = False
                            break

                    if valido and meta_total > 0:
                        return meta_total

        return 0.0

    @classmethod
    def _es_salto_corte_ruta(
        cls, origen: str, destino: str, sentido_actual: str = "Ida", nombre_ruta: str = "El Arbolito"
    ) -> bool:
        """Detecta si el salto entre 'origen' y 'destino' es una salida de la ruta regular."""
        if str(nombre_ruta).strip().lower() == "agua salada":
            cortes = set(RutasConfig.CORTE_AGUA_SALADA)
        else:
            cortes = set(RutasConfig.CORTE_EL_ARBOLITO)

        if origen in cortes:
            return False

        if destino in cortes:
            return True

        secuencias = cls._obtener_secuencias_por_ruta(nombre_ruta)

        for secuencia in secuencias:
            if origen in secuencia and destino in secuencia:
                idx_orig = secuencia.index(origen)
                idx_dest = secuencia.index(destino)

                if sentido_actual == "Ida":
                    if 0 < (idx_dest - idx_orig) <= 3:
                        return False
                elif sentido_actual == "Regreso":
                    if 0 < (idx_orig - idx_dest) <= 3:
                        return False

                if idx_dest > idx_orig and (idx_dest - idx_orig) <= 3:
                    return False

        return True

    @classmethod
    def obtener_resumen_diario_unidades(
        cls, df_completo: pd.DataFrame
    ) -> pd.DataFrame:
        """Genera un resumen diario por unidad con horarios, duración y kilometraje."""
        if df_completo is None or df_completo.empty:
            return pd.DataFrame()

        col_agrupacion = next(
            (c for c in df_completo.columns if any(k in c.upper() for k in ["AGRUPA", "UNIDAD", "VEHICU"])),
            df_completo.columns[0]
        )
        col_geocerca = next(
            (c for c in df_completo.columns if "GEOCERCA" in c.upper() or "PUNTO" in c.upper()),
            "Geocerca" if "Geocerca" in df_completo.columns else df_completo.columns[1]
        )

        primeras_filas = []

        for unidad, df_u in df_completo.groupby(col_agrupacion, sort=False):
            if not df_u.empty:
                mask_resumen = df_u[col_geocerca].astype(str).str.strip() == "-----"
                row_0 = (
                    df_u[mask_resumen].iloc[0]
                    if mask_resumen.any()
                    else df_u.iloc[0]
                )

                h_in = row_0.get("Hora de entrada", row_0.get("Entrada", "-"))
                h_out = row_0.get("Hora de salida", row_0.get("Salida", "-"))
                duracion = row_0.get("Tiempo total", row_0.get("Duración en", "-"))
                km = row_0.get("Kilometraje", "-")

                str_h_in = (
                    h_in.strftime("%d.%m.%Y %H:%M:%S")
                    if hasattr(h_in, "strftime")
                    else str(h_in)
                )
                str_h_out = (
                    h_out.strftime("%d.%m.%Y %H:%M:%S")
                    if hasattr(h_out, "strftime")
                    else str(h_out)
                )

                primeras_filas.append(
                    {
                        "Agrupación": unidad,
                        "Hora_Inicio": str_h_in,
                        "Hora_Termino": str_h_out,
                        "Tiempo_Total": str(duracion if pd.notna(duracion) else "-"),
                        "Kilometraje": str(km if pd.notna(km) else "-"),
                    }
                )

        return pd.DataFrame(primeras_filas)

    # =========================================================================
    # SECCIÓN B: CÁLCULOS Y ANÁLISIS DE UNIDADES
    # =========================================================================

    @classmethod
    def procesar_unidad(
        cls, df_unidad: pd.DataFrame, tiempos_objetivo: dict = None, nombre_ruta: str = "El Arbolito"
    ) -> pd.DataFrame:
        """Analiza cronológicamente el recorrido de una unidad clasificando correctamente los desvíos de ruta."""
        if df_unidad is None or df_unidad.empty:
            return pd.DataFrame()

        cols = list(df_unidad.columns)
        col_agrupacion = next(
            (c for c in cols if any(k in c.upper() for k in ["AGRUPA", "UNIDAD", "VEHICU"])),
            cols[0]
        )
        col_geocerca = next(
            (c for c in cols if any(k in c.upper() for k in ["GEOCERCA", "PUNTO", "LUGAR"])),
            cols[1] if len(cols) > 1 else cols[0]
        )
        col_salida = next(
            (c for c in cols if "SALIDA" in c.upper()),
            next((c for c in cols if any(k in c.upper() for k in ["HORA", "FECHA", "TIEMPO"])), None)
        )
        col_entrada = next((c for c in cols if "ENTRADA" in c.upper()), col_salida)

        if not col_salida:
            col_salida = cols[2] if len(cols) > 2 else cols[-1]

        unidad_id = str(df_unidad[col_agrupacion].iloc[0])

        df_registros = df_unidad[
            df_unidad[col_geocerca].astype(str).str.strip() != "-----"
        ].copy()

        if df_registros.empty:
            return pd.DataFrame()

        df_registros["Hora_Salida_Dt"] = pd.to_datetime(
            df_registros[col_salida], dayfirst=True, errors="coerce"
        )
        df_registros = df_registros.dropna(subset=["Hora_Salida_Dt"]).sort_values(
            by="Hora_Salida_Dt", ascending=True
        )

        if df_registros.empty:
            return pd.DataFrame()

        # Extraer catálogo estricto de geocercas de la ruta activa
        secuencias_ruta = cls._obtener_secuencias_por_ruta(nombre_ruta)
        geocercas_permitidas_ruta = {geo for sec in secuencias_ruta for geo in sec}

        if str(nombre_ruta).strip().lower() == "agua salada":
            cortes_ruta = set(RutasConfig.CORTE_AGUA_SALADA)
            puntos_inicio = set(RutasConfig.PUNTOS_INICIO_AGUA_SALADA)
            puntos_retorno = {"AguaSalada"}
        else:
            cortes_ruta = set(RutasConfig.CORTE_EL_ARBOLITO)
            puntos_inicio = set(RutasConfig.PUNTOS_INICIO_EL_ARBOLITO)
            puntos_retorno = {"CTM", "Gavilan"}

        primer_geo = str(df_registros[col_geocerca].iloc[0]).strip()
        if primer_geo in puntos_retorno:
            sentido_actual = "Regreso"
            toco_terminal_retorno = True
        else:
            sentido_actual = "Ida"
            toco_terminal_retorno = False

        filas_procesadas = []
        prev_row = None
        vuelta_actual = 1

        # =====================================================================
        # BUCLE PRINCIPAL DE REGISTROS
        # =====================================================================
        for _, row in df_registros.iterrows():
            curr_geo = str(row.get(col_geocerca, "")).strip()

            hora_in_val = row.get(col_entrada)
            hora_in_str = (
                hora_in_val.strftime("%d.%m.%Y %H:%M:%S")
                if hasattr(hora_in_val, "strftime")
                else str(hora_in_val if pd.notna(hora_in_val) else "-")
            )
            hora_out_str = (
                row.get("Hora_Salida_Dt").strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(row.get("Hora_Salida_Dt"), "strftime")
                else str(row.get(col_salida, "-"))
            )

            # -----------------------------------------------------------------
            # VALIDACIÓN DE GEOCERCA PERTENECIENTE A LA RUTA (DESVÍO DE RUTA)
            # -----------------------------------------------------------------
            es_desvio = curr_geo not in geocercas_permitidas_ruta and curr_geo not in cortes_ruta

            # Primer registro
            if prev_row is None:
                estado_ini = "DESVÍO DE RUTA" if es_desvio else "Inicio de Ruta"
                tipo_ini = "Desvío" if es_desvio else "Normal"
                eval_ini = "Desvío de Ruta" if es_desvio else "A Tiempo"

                filas_procesadas.append(
                    {
                        "Agrupación": unidad_id,
                        "Geocerca": curr_geo,
                        "Entrada": hora_in_str,
                        "Salida": hora_out_str,
                        "Tiempo_Real": "Punto Inicial",
                        "Tiempo_Estimado": "-",
                        "Desfase": "-",
                        "Estado_Ruta": estado_ini,
                        "Vuelta_Num": vuelta_actual,
                        "Sentido": sentido_actual,
                        "Tipo": tipo_ini,
                        "Evaluacion_Tiempo": eval_ini,
                        "Hora de salida": row.get("Hora_Salida_Dt"),
                        "Segundos_Retraso": 0.0,
                    }
                )
                prev_row = row
                continue

            prev_geo = str(prev_row.get(col_geocerca, "")).strip()
            prev_geo_clean = prev_geo.replace(" (Faltante)", "").strip()

            segundos_transcurridos = (
                (row["Hora_Salida_Dt"] - prev_row["Hora_Salida_Dt"]).total_seconds()
            )

            # CONTROL DE SENTIDO Y VUELTAS
            if curr_geo in puntos_retorno:
                sentido_actual = "Regreso"
                toco_terminal_retorno = True
            elif curr_geo in puntos_inicio:
                if sentido_actual == "Regreso" or toco_terminal_retorno:
                    vuelta_actual += 1
                    toco_terminal_retorno = False
                sentido_actual = "Ida"

            # 1. Geocercas Repetidas
            if curr_geo == prev_geo_clean:
                filas_procesadas.append(
                    {
                        "Agrupación": unidad_id,
                        "Geocerca": curr_geo,
                        "Entrada": hora_in_str,
                        "Salida": hora_out_str,
                        "Tiempo_Real": cls._formatear_min_seg(segundos_transcurridos),
                        "Tiempo_Estimado": "-",
                        "Desfase": "Tiempo GeoRep",
                        "Estado_Ruta": "Geocerca Repetida",
                        "Vuelta_Num": vuelta_actual,
                        "Sentido": sentido_actual,
                        "Tipo": "Repetida",
                        "Evaluacion_Tiempo": f"{cls._formatear_min_seg(segundos_transcurridos)} (GeoRep)",
                        "Hora de salida": row.get("Hora_Salida_Dt"),
                        "Segundos_Retraso": 0.0,
                    }
                )
                prev_row = row
                continue

            # 2. Manejo de Desvío de Ruta Explícito (Geocerca ajena)
            if es_desvio:
                filas_procesadas.append(
                    {
                        "Agrupación": unidad_id,
                        "Geocerca": curr_geo,
                        "Entrada": hora_in_str,
                        "Salida": hora_out_str,
                        "Tiempo_Real": cls._formatear_min_seg(segundos_transcurridos),
                        "Tiempo_Estimado": "-",
                        "Desfase": "-",
                        "Estado_Ruta": "DESVÍO DE RUTA",
                        "Vuelta_Num": vuelta_actual,
                        "Sentido": sentido_actual,
                        "Tipo": "Desvío",
                        "Evaluacion_Tiempo": "Desvío de Ruta",
                        "Hora de salida": row.get("Hora_Salida_Dt"),
                        "Segundos_Retraso": 0.0,
                    }
                )
                prev_row = row
                continue

            faltantes = cls._obtener_secuencia_intermedia(prev_geo_clean, curr_geo, nombre_ruta)

            # 3. Detección de Anomalías de Secuencia
            if str(nombre_ruta).strip().lower() == "el arbolito":
                es_paso_ctm_gavilan = (
                    (prev_geo_clean == "CTM" and curr_geo == "Gavilan") or
                    (prev_geo_clean == "Gavilan" and curr_geo == "CTM") or
                    (prev_geo_clean == "Centro" and curr_geo == "CTM")
                )
            else:
                es_paso_ctm_gavilan = False

            if es_paso_ctm_gavilan:
                es_anomalia = False
            else:
                anomalia_ida = (curr_geo in puntos_retorno) and (
                    len(faltantes) >= 2 or prev_geo_clean in puntos_inicio
                )
                anomalia_regreso = (curr_geo in puntos_inicio) and (
                    len(faltantes) >= 2 or prev_geo_clean in puntos_retorno
                )
                es_anomalia = anomalia_ida or anomalia_regreso

            # 4. Cortes de Ruta
            es_corte_config = curr_geo in cortes_ruta
            es_salto_atipico = cls._es_salto_corte_ruta(prev_geo_clean, curr_geo, sentido_actual, nombre_ruta)

            if (es_corte_config or es_salto_atipico) and not es_anomalia and not es_paso_ctm_gavilan:
                filas_procesadas.append(
                    {
                        "Agrupación": unidad_id,
                        "Geocerca": curr_geo,
                        "Entrada": hora_in_str,
                        "Salida": hora_out_str,
                        "Tiempo_Real": cls._formatear_min_seg(segundos_transcurridos),
                        "Tiempo_Estimado": "-",
                        "Desfase": "Tiempo Corte",
                        "Estado_Ruta": "CORTE RUTA",
                        "Vuelta_Num": vuelta_actual,
                        "Sentido": sentido_actual,
                        "Tipo": "Corte",
                        "Evaluacion_Tiempo": "Corte de Ruta",
                        "Hora de salida": row.get("Hora_Salida_Dt"),
                        "Segundos_Retraso": 0.0,
                    }
                )
                prev_row = row
                continue

            # 5. Geocercas Omitidas
            if faltantes and not es_anomalia:
                for geo_falta in faltantes:
                    filas_procesadas.append(
                        {
                            "Agrupación": unidad_id,
                            "Geocerca": f"{geo_falta} (Faltante)",
                            "Entrada": "-",
                            "Salida": "-",
                            "Tiempo_Real": "-",
                            "Tiempo_Estimado": "-",
                            "Desfase": "-",
                            "Estado_Ruta": "NO REGISTRADA",
                            "Vuelta_Num": vuelta_actual,
                            "Sentido": sentido_actual,
                            "Tipo": "Omitida",
                            "Evaluacion_Tiempo": "Omision",
                            "Hora de salida": row.get("Hora_Salida_Dt"),
                            "Segundos_Retraso": 0.0,
                        }
                    )

            # 6. Evaluación Normal de Tiempos
            meta_min = cls._calcular_meta_acumulada(
                prev_geo_clean, curr_geo, tiempos_objetivo, nombre_ruta
            )
            str_tiempo_real = cls._formatear_min_seg(segundos_transcurridos)
            segs_retraso = 0.0

            if meta_min > 0 and not es_anomalia:
                meta_seg = meta_min * 60.0
                str_meta = cls._formatear_min_seg(meta_seg)
                dif_seg = segundos_transcurridos - meta_seg
                str_dif = cls._formatear_min_seg(abs(dif_seg))
                signo = "+" if dif_seg > 0 else "-"
                str_desfase = f"{signo}{str_dif}"

                if dif_seg > 60:
                    eval_categoria = "Retraso"
                    segs_retraso = dif_seg
                elif dif_seg < -60:
                    eval_categoria = "Adelanto"
                else:
                    eval_categoria = "A Tiempo"

                eval_str = f"{eval_categoria} | {str_tiempo_real} / Meta: {str_meta} (Dif: {signo}{str_dif})"
            else:
                str_meta = "-"
                str_desfase = "-"
                eval_categoria = "ANOMALÍA" if es_anomalia else "A Tiempo"
                eval_str = f"{eval_categoria} | {str_tiempo_real}"

            filas_procesadas.append(
                {
                    "Agrupación": unidad_id,
                    "Geocerca": curr_geo,
                    "Entrada": hora_in_str,
                    "Salida": hora_out_str,
                    "Tiempo_Real": str_tiempo_real,
                    "Tiempo_Estimado": str_meta,
                    "Desfase": str_desfase,
                    "Estado_Ruta": "ANOMALÍA" if es_anomalia else "Ruta Correcta",
                    "Vuelta_Num": vuelta_actual,
                    "Sentido": sentido_actual,
                    "Tipo": "Anomalía" if es_anomalia else "Normal",
                    "Evaluacion_Tiempo": eval_str,
                    "Hora de salida": row.get("Hora_Salida_Dt"),
                    "Segundos_Retraso": segs_retraso,
                }
            )

            prev_row = row

        return pd.DataFrame(filas_procesadas)

    @classmethod
    def analizar_unidades(
        cls, df_completo: pd.DataFrame, tiempos_objetivo: dict = None, nombre_ruta: str = "El Arbolito"
    ) -> pd.DataFrame:
        """Analiza todas las unidades y concatena los resultados."""
        if df_completo is None or df_completo.empty:
            return pd.DataFrame()

        col_agrupacion = next(
            (c for c in df_completo.columns if any(k in c.upper() for k in ["AGRUPA", "UNIDAD", "VEHICU"])),
            df_completo.columns[0]
        )

        lista_procesada = []
        for _, df_u in df_completo.groupby(col_agrupacion, sort=False):
            df_u_proc = cls.procesar_unidad(df_u, tiempos_objetivo, nombre_ruta=nombre_ruta)
            if not df_u_proc.empty:
                lista_procesada.append(df_u_proc)

        return (
            pd.concat(lista_procesada, ignore_index=True)
            if lista_procesada
            else pd.DataFrame()
        )

    # =========================================================================
    # SECCIÓN C: ESTADÍSTICAS Y ANÁLISIS DE RETRASOS
    # =========================================================================

    @classmethod
    def obtener_top_5_retrasos(cls, df_resultado: pd.DataFrame) -> pd.DataFrame:
        """Extrae los 5 mayores retrasos individuales registrados por tramo/geocerca."""
        if df_resultado is None or df_resultado.empty:
            return pd.DataFrame(columns=["Unidad", "Geocerca", "Retraso_Minutos", "Formato"])

        if "Segundos_Retraso" not in df_resultado.columns:
            return pd.DataFrame()

        df_retrasos = df_resultado[df_resultado["Segundos_Retraso"] > 0].copy()

        if df_retrasos.empty:
            return pd.DataFrame()

        top_5 = df_retrasos.sort_values(by="Segundos_Retraso", ascending=False).head(5)

        resultado = []
        for _, row in top_5.iterrows():
            segs = row["Segundos_Retraso"]
            resultado.append(
                {
                    "Unidad": row.get("Agrupación", "-"),
                    "Geocerca": row.get("Geocerca", "-"),
                    "Retraso_Minutos": round(segs / 60.0, 2),
                    "Formato": cls._formatear_min_seg(segs),
                }
            )

        return pd.DataFrame(resultado)

    @classmethod
    def obtener_acumulado_retrasos_por_unidad(
        cls, df_resultado: pd.DataFrame
    ) -> pd.DataFrame:
        """Calcula el tiempo total acumulado de retraso para cada unidad analizada."""
        if df_resultado is None or df_resultado.empty or "Segundos_Retraso" not in df_resultado.columns:
            return pd.DataFrame(columns=["Unidad", "Minutos_Acumulados", "Formato"])

        agrupado = (
            df_resultado.groupby("Agrupación")["Segundos_Retraso"]
            .sum()
            .reset_index()
        )

        agrupado["Minutos_Acumulados"] = (agrupado["Segundos_Retraso"] / 60.0).round(2)
        agrupado["Formato"] = agrupado["Segundos_Retraso"].apply(cls._formatear_min_seg)
        agrupado.rename(columns={"Agrupación": "Unidad"}, inplace=True)

        return agrupado.sort_values(by="Minutos_Acumulados", ascending=False)