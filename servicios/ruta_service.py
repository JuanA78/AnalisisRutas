# servicios/ruta_service.py
import warnings
import pandas as pd
from configuracion.rutas_config import RutasConfig

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class RutaService:

    @staticmethod
    def _formatear_min_seg(segundos: float) -> str:
        if pd.isna(segundos) or segundos < 0:
            return "-"
        tot_seg = int(round(segundos))
        minutos = tot_seg // 60
        segs = tot_seg % 60
        return f"{minutos}m {segs:02d}s"

    @staticmethod
    def _obtener_secuencia_intermedia(origen: str, destino: str) -> list:
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

    @classmethod
    def obtener_resumen_diario_unidades(
        cls, df_completo: pd.DataFrame
    ) -> pd.DataFrame:
        if df_completo is None or df_completo.empty:
            return pd.DataFrame()

        col_agrupacion = (
            "Agrupación" if "Agrupación" in df_completo.columns else df_completo.columns[0]
        )
        col_geocerca = next(
            (c for c in df_completo.columns if "GEOCERCA" in c.upper() or "PUNTO" in c.upper()),
            "Geocerca" if "Geocerca" in df_completo.columns else df_completo.columns[1]
        )

        primeras_filas = []
        for unidad, df_u in df_completo.groupby(col_agrupacion, sort=False):
            if not df_u.empty:
                mask_resumen = (
                    df_u[col_geocerca].astype(str).str.strip() == "-----"
                )
                row_0 = (
                    df_u[mask_resumen].iloc[0]
                    if mask_resumen.any()
                    else df_u.iloc[0]
                )

                h_in = row_0.get("Hora de entrada", "-")
                h_out = row_0.get("Hora de salida", "-")
                duracion = row_0.get(
                    "Tiempo total", row_0.get("Duración en", "-")
                )
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
                        "Tiempo_Total": str(
                            duracion if pd.notna(duracion) else "-"
                        ),
                        "Kilometraje": str(km if pd.notna(km) else "-"),
                    }
                )

        return pd.DataFrame(primeras_filas)

    @classmethod
    def procesar_unidad(
        cls, df_unidad: pd.DataFrame, tiempos_objetivo: dict = None
    ) -> pd.DataFrame:
        if df_unidad is None or df_unidad.empty:
            return pd.DataFrame()

        col_agrupacion = (
            "Agrupación" if "Agrupación" in df_unidad.columns else df_unidad.columns[0]
        )
        col_geocerca = next(
            (c for c in df_unidad.columns if "GEOCERCA" in c.upper() or "PUNTO" in c.upper()),
            "Geocerca" if "Geocerca" in df_unidad.columns else df_unidad.columns[1]
        )
        col_salida = next(
            (c for c in df_unidad.columns if "SALIDA" in c.upper()),
            "Hora de salida"
        )
        col_entrada = next(
            (c for c in df_unidad.columns if "ENTRADA" in c.upper()),
            "Hora de entrada"
        )

        unidad_id = str(df_unidad[col_agrupacion].iloc[0])

        df_registros = df_unidad[
            df_unidad[col_geocerca].astype(str).str.strip() != "-----"
        ].copy()
        if df_registros.empty:
            return pd.DataFrame()

        df_registros["Hora_Salida_Dt"] = pd.to_datetime(
            df_registros[col_salida], dayfirst=True, errors="coerce"
        )
        df_registros = df_registros.dropna(
            subset=["Hora_Salida_Dt"]
        ).sort_values(by="Hora_Salida_Dt", ascending=True)

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

        # ---------------------------------------------------------------------
        # DETECCIÓN CORRECTA DEL SENTIDO INICIAL SEGÚN EL PRIMER REGISTRO
        # ---------------------------------------------------------------------
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
                        "Evaluacion_Tiempo": "-",
                        "Hora de salida": row.get("Hora_Salida_Dt"),
                    }
                )
                prev_row = row
                continue

            prev_geo = str(prev_row.get(col_geocerca, "")).strip()
            prev_geo_clean = prev_geo.replace(" (Faltante)", "").strip()

            segundos_transcurridos = (
                (row["Hora_Salida_Dt"] - prev_row["Hora_Salida_Dt"]).total_seconds()
            )

            # Transición de Sentido y Conteo de Vuelta
            if curr_geo in ["CTM", "Gavilan", "AguaSalada"]:
                sentido_actual = "Regreso"
                toco_terminal_retorno = True
            elif curr_geo in ["La Cruz", "Canal_CasaEloy"]:
                if sentido_actual == "Regreso" or toco_terminal_retorno:
                    vuelta_actual += 1
                    toco_terminal_retorno = False
                sentido_actual = "Ida"

            # 1. Geocerca Repetida
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
                    }
                )
                prev_row = row
                continue

            # 2. Corte de Ruta
            if curr_geo in cortes_ruta:
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
                        "Evaluacion_Tiempo": f"{cls._formatear_min_seg(segundos_transcurridos)} (Corte)",
                        "Hora de salida": row.get("Hora_Salida_Dt"),
                    }
                )
                prev_row = row
                continue

            # 3. Geocercas Omitidas
            faltantes = cls._obtener_secuencia_intermedia(prev_geo_clean, curr_geo)
            es_reinicio = len(faltantes) >= 3 and curr_geo in puntos_inicio

            if faltantes and not es_reinicio:
                for geo_falta in faltantes:
                    filas_procesadas.append(
                        {
                            "Agrupación": unidad_id,
                            "Geocerca": f"{geo_falta} (Faltante)",
                            "Entrada": "-",
                            "Salida": "-",
                            "Tiempo_Real": "Punto Inicial",
                            "Tiempo_Estimado": "-",
                            "Desfase": "-",
                            "Estado_Ruta": "NO REGISTRADA",
                            "Vuelta_Num": vuelta_actual,
                            "Sentido": sentido_actual,
                            "Tipo": "Omitida",
                            "Evaluacion_Tiempo": "Sin Registro (Omitida)",
                            "Hora de salida": row.get("Hora_Salida_Dt"),
                        }
                    )

            # 4. Fila Normal Evaluada
            meta_min = cls._calcular_meta_acumulada(
                prev_geo_clean, curr_geo, tiempos_objetivo
            )
            str_tiempo_real = cls._formatear_min_seg(segundos_transcurridos)

            if meta_min > 0 and not es_reinicio:
                meta_seg = meta_min * 60.0
                str_meta = cls._formatear_min_seg(meta_seg)
                dif_seg = segundos_transcurridos - meta_seg
                str_dif = cls._formatear_min_seg(abs(dif_seg))
                signo = "+" if dif_seg > 0 else "-"
                str_desfase = f"{signo}{str_dif}"
                eval_str = f"{str_tiempo_real} / Meta: {str_meta} (Dif: {signo}{str_dif})"
            else:
                str_meta = "-"
                str_desfase = "-"
                eval_str = f"{str_tiempo_real} (Salida ➔ Salida)"

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
                    "Tipo": "Normal",
                    "Evaluacion_Tiempo": eval_str,
                    "Hora de salida": row.get("Hora_Salida_Dt"),
                }
            )
            prev_row = row

        return pd.DataFrame(filas_procesadas)

    @classmethod
    def analizar_unidades(
        cls, df_completo: pd.DataFrame, tiempos_objetivo: dict = None
    ) -> pd.DataFrame:
        if df_completo is None or df_completo.empty:
            return pd.DataFrame()
        
        col_agrupacion = (
            "Agrupación" if "Agrupación" in df_completo.columns else df_completo.columns[0]
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