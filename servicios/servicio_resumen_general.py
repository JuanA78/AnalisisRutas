import pandas as pd
from servicios.servicio_actividad_gps import ServicioActividadGPS


class ServicioResumenGeneral:
    """Consolida las métricas del Resumen General delegando cada cálculo a su servicio correspondiente."""

    @staticmethod
    def _normalizar_id(texto) -> str:
        if pd.isna(texto):
            return ""
        return str(texto).replace("-", "").strip().upper()

    @classmethod
    def preparar_resumen_general(
        cls,
        df_resumen_diario: pd.DataFrame,
        df_resultado_geocercas: pd.DataFrame,
        df_actividad_gps: pd.DataFrame = None
    ) -> pd.DataFrame:
        """
        Consolida la tabla del Resumen General.
        - Cálculos de geocercas, horarios y conteos vienen de RutaService.
        - Las 3 métricas de mensajes GPS vienen de ServicioActividadGPS.
        """
        columnas_finales = [
            "Unidad", "Hora Inicio", "Hora Término", "Tiempo Total",
            "A Tiempo", "Retrasos", "Adelantos", "Omisiones",
            "Km Actividad Diaria", "Velocidad Máx.", "Tiempo Viajes GPS"
        ]

        if df_resumen_diario is None or df_resumen_diario.empty:
            return pd.DataFrame(columns=columnas_finales)

        resumen = df_resumen_diario.copy()

        # Normalizar nombres de columnas principales
        equivalencias = {
            "Agrupación": "Unidad",
            "Agrupacion": "Unidad",
            "Hora_Inicio": "Hora Inicio",
            "Hora_Termino": "Hora Término",
            "Tiempo_Total": "Tiempo Total",
            "Kilometraje": "Km Actividad Diaria"
        }
        resumen.rename(columns=equivalencias, inplace=True)

        if "Unidad" not in resumen.columns:
            resumen["Unidad"] = ""

        # Contadores calculados por RutaService en df_resultado_geocercas
        resumen["A Tiempo"] = 0
        resumen["Retrasos"] = 0
        resumen["Adelantos"] = 0
        resumen["Omisiones"] = 0

        if df_resultado_geocercas is not None and not df_resultado_geocercas.empty and "Agrupación" in df_resultado_geocercas.columns:
            col_agrupa = "Agrupación"

            for idx, fila in resumen.iterrows():
                u_norm = cls._normalizar_id(fila["Unidad"])
                if not u_norm:
                    continue

                datos_u = df_resultado_geocercas[
                    df_resultado_geocercas[col_agrupa].apply(
                        lambda val: u_norm in cls._normalizar_id(val) or cls._normalizar_id(val) in u_norm
                    )
                ]

                if datos_u.empty:
                    continue

                if "Evaluacion_Tiempo" in datos_u.columns:
                    evals = datos_u["Evaluacion_Tiempo"].fillna("").astype(str).str.upper()
                    resumen.at[idx, "A Tiempo"] = int(evals.str.contains("A TIEMPO", regex=False).sum())
                    resumen.at[idx, "Retrasos"] = int(evals.str.contains("RETRASO", regex=False).sum())
                    resumen.at[idx, "Adelantos"] = int(evals.str.contains("ADELANTO", regex=False).sum())

                omisiones = pd.Series(False, index=datos_u.index)
                if "Tipo" in datos_u.columns:
                    omisiones |= datos_u["Tipo"].fillna("").astype(str).str.upper().str.contains("OMITID", regex=True)
                if "Estado_Ruta" in datos_u.columns:
                    omisiones |= datos_u["Estado_Ruta"].fillna("").astype(str).str.upper().str.contains("NO REGISTRADA|FALTANTE", regex=True)

                resumen.at[idx, "Omisiones"] = int(omisiones.sum())

        # Obtener exclusivamente las 3 métricas requeridas desde ServicioActividadGPS
        metricas_gps = ServicioActividadGPS.obtener_metricas_resumen(df_actividad_gps)

        resumen["Velocidad Máx."] = "-"
        resumen["Tiempo Viajes GPS"] = "-"

        for idx, fila in resumen.iterrows():
            u_norm = cls._normalizar_id(fila["Unidad"])
            if u_norm in metricas_gps:
                datos_gps = metricas_gps[u_norm]
                # Si el kilometraje venía vacío del de geocercas, usar el de GPS
                if str(resumen.at[idx, "Km Actividad Diaria"]).strip() in ["-", "", "0.0", "0 km"]:
                    resumen.at[idx, "Km Actividad Diaria"] = datos_gps["km"]
                resumen.at[idx, "Velocidad Máx."] = datos_gps["velocidad_max"]
                resumen.at[idx, "Tiempo Viajes GPS"] = datos_gps["tiempo_viajes"]

        for col in columnas_finales:
            if col not in resumen.columns:
                resumen[col] = "-"

        return resumen[columnas_finales].copy()

    @classmethod
    def obtener_top_5_retrasos_unidad(
        cls, df_resultado_geocercas: pd.DataFrame, unidad_id: str
    ) -> list:
        """Obtiene los 5 retrasos más altos calculados por RutaService para la unidad requerida."""
        if df_resultado_geocercas is None or df_resultado_geocercas.empty:
            return []

        if "Agrupación" not in df_resultado_geocercas.columns or "Segundos_Retraso" not in df_resultado_geocercas.columns:
            return []

        u_norm = cls._normalizar_id(unidad_id)
        if not u_norm:
            return []

        mascara = df_resultado_geocercas["Agrupación"].apply(
            lambda val: u_norm in cls._normalizar_id(val) or cls._normalizar_id(val) in u_norm
        ) & (df_resultado_geocercas["Segundos_Retraso"] > 0)

        df_u = df_resultado_geocercas.loc[mascara].copy()

        if df_u.empty:
            return []

        top5_df = df_u.sort_values(by="Segundos_Retraso", ascending=False).head(5)

        detalles = []
        for _, row in top5_df.iterrows():
            detalles.append({
                "geocerca": row.get("Geocerca", "-"),
                "hora": row.get("Salida", row.get("Entrada", "-")),
                "desfase": row.get("Desfase", "-"),
                "evaluacion": row.get("Evaluacion_Tiempo", "-")
            })

        return detalles