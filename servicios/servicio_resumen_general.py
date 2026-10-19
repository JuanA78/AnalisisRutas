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
        Consolida la tabla del Resumen General con la columna Min. Retraso Acum.
        y la Velocidad Máxima real enviada por ServicioActividadGPS.
        """
        columnas_finales = [
            "Unidad", "Hora Inicio", "Hora Término", "Tiempo Total",
            "A Tiempo", "Retrasos", "Adelantos", "Omisiones", "Min. Retraso Acum.",
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

        # Inicializar contadores
        resumen["A Tiempo"] = 0
        resumen["Retrasos"] = 0
        resumen["Adelantos"] = 0
        resumen["Omisiones"] = 0
        resumen["Min. Retraso Acum."] = "0m"

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

                # Conteo de Omisiones
                omisiones = pd.Series(False, index=datos_u.index)
                if "Tipo" in datos_u.columns:
                    omisiones |= datos_u["Tipo"].fillna("").astype(str).str.upper().str.contains("OMITID", regex=True)
                if "Estado_Ruta" in datos_u.columns:
                    omisiones |= datos_u["Estado_Ruta"].fillna("").astype(str).str.upper().str.contains("NO REGISTRADA|FALTANTE", regex=True)

                resumen.at[idx, "Omisiones"] = int(omisiones.sum())

                # Cálculo de Minutos de Retraso Acumulado
                if "Segundos_Retraso" in datos_u.columns:
                    total_segundos = datos_u.loc[datos_u["Segundos_Retraso"] > 0, "Segundos_Retraso"].sum()
                    minutos = int(total_segundos // 60)
                    segundos = int(total_segundos % 60)
                    resumen.at[idx, "Min. Retraso Acum."] = f"{minutos}m {segundos}s" if segundos > 0 else f"{minutos}m"

      # Métricas desde ServicioActividadGPS
        metricas_gps = ServicioActividadGPS.obtener_metricas_resumen(df_actividad_gps)

        for idx, fila in resumen.iterrows():
            u_norm = cls._normalizar_id(fila["Unidad"])
            if u_norm in metricas_gps:
                datos_gps = metricas_gps[u_norm]
                
                # Asignación directa e incondicional desde el reporte GPS
                resumen.at[idx, "Km Actividad Diaria"] = datos_gps["km"]
                resumen.at[idx, "Velocidad Máx."] = datos_gps["velocidad_max"]
                resumen.at[idx, "Tiempo Viajes GPS"] = datos_gps["tiempo_viajes"]

        # Garantizar valores por defecto (-) si alguna columna quedó vacía o ausente
        for col in columnas_finales:
            if col not in resumen.columns:
                resumen[col] = "-"
            else:
                resumen[col] = resumen[col].fillna("-")

        return resumen[columnas_finales].copy()

    @classmethod
    def obtener_top_5_retrasos_unidad(
        cls, df_resultado_geocercas: pd.DataFrame, unidad_id: str
    ) -> list:
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