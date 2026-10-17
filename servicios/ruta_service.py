import warnings
import pandas as pd
from configuracion.rutas_config import RutasConfig

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class RutaService:
    """
    Servicio encargado de procesar y analizar los recorridos de las unidades.
    Identifica vueltas, cortes, geocercas omitidas, evalúa tiempos y calcula
    estadísticas acumuladas de retrasos.
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
    def _obtener_secuencia_intermedia(origen: str, destino: str) -> list:
        """Obtiene las geocercas que deberían estar entre origen y destino."""
        secuencias = (
            RutasConfig.SECUENCIAS_EL_ARBOLITO
            + RutasConfig.SECUENCIAS_AGUA_SALADA
        )

        for secuencia in secuencias:
            if origen in secuencia and destino in secuencia:
                idx_orig = secuencia.index(origen)
                idx_dest = secuencia.index(destino)

                if idx_dest > idx_orig + 1:
                    return secuencia[idx_orig + 1 : idx_dest]

        return []

    @staticmethod
    def _calcular_meta_acumulada(
        origen: str, destino: str, tiempos_objetivo: dict
    ) -> float:
        """Calcula el tiempo objetivo directo o acumulado entre dos geocercas."""
        if not tiempos_objetivo:
            return 0.0

        if (origen, destino) in tiempos_objetivo:
            return float(tiempos_objetivo[(origen, destino)])

        secuencias = (
            RutasConfig.SECUENCIAS_EL_ARBOLITO
            + RutasConfig.SECUENCIAS_AGUA_SALADA
        )

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

    @staticmethod
    def _es_salto_corte_ruta(origen: str, destino: str, sentido_actual: str = "Ida") -> bool:
        """
        Detecta si el salto entre 'origen' y 'destino' es una salida de la ruta regular.
        Si el origen o el destino son puntos de corte, se manejan de forma independiente.
        """
        # Si el origen fue un punto de corte, el destino actual es la reincorporación a la ruta
        if origen in RutasConfig.CORTE_EL_ARBOLITO or origen in RutasConfig.CORTE_AGUA_SALADA:
            return False

        # Si el destino es un punto de corte explícito, sí es un corte de ruta
        if destino in RutasConfig.CORTE_EL_ARBOLITO or destino in RutasConfig.CORTE_AGUA_SALADA:
            return True

        secuencias = (
            RutasConfig.SECUENCIAS_EL_ARBOLITO
            + RutasConfig.SECUENCIAS_AGUA_SALADA
        )

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
        """
        Genera un resumen diario por unidad con sus horarios de inicio y término,
        duración total y kilometraje.
        """
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
        cls, df_unidad: pd.DataFrame, tiempos_objetivo: dict = None
    ) -> pd.DataFrame:
        """Analiza cronológicamente el recorrido de una unidad."""
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

        # Excluir renglones resumen de encabezado ("-----")
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

        geocercas_unicas = (
            df_registros[col_geocerca].astype(str).str.strip().unique()
        )
        es_agua_salada = any(
            g in RutasConfig.EJE_X_AGUA_SALADA for g in geocercas_unicas
        )

        cortes_ruta = (
            RutasConfig.CORTE_AGUA_SALADA
            if es_agua_salada
            else RutasConfig.CORTE_EL_ARBOLITO
        )
        puntos_inicio = (
            RutasConfig.PUNTOS_INICIO_AGUA_SALADA
            if es_agua_salada
            else RutasConfig.PUNTOS_INICIO_EL_ARBOLITO
        )

        primer_geo = str(df_registros[col_geocerca].iloc[0]).strip()
        if primer_geo in ["CTM", "Gavilan", "AguaSalada"]:
            sentido_actual = "Regreso"
            toco_terminal_retorno = True
        else:
            sentido_actual = "Ida"
            toco_terminal_retorno = False

        filas_procesadas = []
        prev_row = None
        vuelta_actual = 1

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

            # Primer registro: Punto inicial de la ruta
            if prev_row is None:
                filas_procesadas.append(
                    {
                        "Agrupación": unidad_id,
                        "Geocerca": curr_geo,
                        "Entrada": hora_in_str,
                        "Salida": hora_out_str,
                        "Tiempo_Real": "Punto Inicial",
                        "Tiempo_Estimado": "-",
                        "Desfase": "-",
                        "Estado_Ruta": "Inicio de Ruta",
                        "Vuelta_Num": vuelta_actual,
                        "Sentido": sentido_actual,
                        "Tipo": "Normal",
                        "Evaluacion_Tiempo": "A Tiempo",
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

            # Sentidos y vueltas
            if curr_geo in ["CTM", "Gavilan", "AguaSalada"]:
                sentido_actual = "Regreso"
                toco_terminal_retorno = True
            elif curr_geo in ["La Cruz", "Canal_CasaEloy"]:
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

            # 2. Detectar si el punto actual es un Reinicio a Terminal de Inicio
            faltantes = cls._obtener_secuencia_intermedia(prev_geo_clean, curr_geo)
            es_reinicio = (curr_geo in puntos_inicio) and (
                len(faltantes) >= 2 or prev_geo_clean in ["CTM", "Gavilan", "AguaSalada"]
            )

            # 3. Cortes de Ruta (UNICAMENTE si NO es un reinicio de ruta)
            es_corte_config = curr_geo in cortes_ruta
            es_salto_atipico = cls._es_salto_corte_ruta(prev_geo_clean, curr_geo, sentido_actual)

            if (es_corte_config or es_salto_atipico) and not es_reinicio:
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

            # 4. Registrar Geocercas Omitidas si no fue reinicio
            if faltantes and not es_reinicio:
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

            # 5. Evaluación Normal o Reinicio de Ruta
            meta_min = cls._calcular_meta_acumulada(
                prev_geo_clean, curr_geo, tiempos_objetivo
            )
            str_tiempo_real = cls._formatear_min_seg(segundos_transcurridos)
            segs_retraso = 0.0

            if meta_min > 0 and not es_reinicio:
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
                eval_categoria = "Reinicio" if es_reinicio else "A Tiempo"
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
                    "Estado_Ruta": "Reinicio de Ruta" if es_reinicio else "Ruta Correcta",
                    "Vuelta_Num": vuelta_actual,
                    "Sentido": sentido_actual,
                    "Tipo": "Reinicio" if es_reinicio else "Normal",
                    "Evaluacion_Tiempo": eval_str,
                    "Hora de salida": row.get("Hora_Salida_Dt"),
                    "Segundos_Retraso": segs_retraso,
                }
            )

            prev_row = row

        return pd.DataFrame(filas_procesadas)

    @classmethod
    def analizar_unidades(
        cls, df_completo: pd.DataFrame, tiempos_objetivo: dict = None
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
            df_u_proc = cls.procesar_unidad(df_u, tiempos_objetivo)
            if not df_u_proc.empty:
                lista_procesada.append(df_u_proc)

        return (
            pd.concat(lista_procesada, ignore_index=True)
            if lista_procesada
            else pd.DataFrame()
        )

    # =========================================================================
    # SECCIÓN C: ESTADÍSTICAS Y ANÁLISIS DE RETRASOS (PARA GRÁFICAS)
    # =========================================================================

    @classmethod
    def obtener_top_5_retrasos(cls, df_resultado: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula y extrae los 5 mayores retrasos individuales registrados por tramo/geocerca.
        Ideal para alimentar las gráficas estadisticas.
        """
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
        """
        Calcula el tiempo total acumulado de retraso para cada unidad analizada.
        """
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