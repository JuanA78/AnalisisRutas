# servicios/analiticos_service.py
import re
import pandas as pd


class AnaliticosService:

    @staticmethod
    def es_reporte_semanal(df_unidades: pd.DataFrame) -> bool:
        """Verifica si en la columna 'Tiempo total' o 'Duración en' existen registros con días (ej. '6 días 8:12:02')"""
        if df_unidades is None or df_unidades.empty:
            return False

        cols = [c for c in df_unidades.columns if any(k in str(c).lower() for k in ["tiempo total", "duración", "duracion"])]
        if not cols:
            return False

        for col in cols:
            valores_str = df_unidades[col].astype(str).str.lower()
            if valores_str.str.contains("día|días|dia|dias").any():
                return True
        return False

    @staticmethod
    def consolidar_reporte_semanal(
        df_resultados_acumulados: pd.DataFrame,
    ) -> pd.DataFrame:
        if df_resultados_acumulados is None or df_resultados_acumulados.empty:
            return pd.DataFrame()

        df = df_resultados_acumulados.copy()

        if "Hora de salida" in df.columns:
            df["Fecha"] = pd.to_datetime(
                df["Hora de salida"], dayfirst=True, errors="coerce"
            ).dt.date
        else:
            df["Fecha"] = "Día Operativo"

        resumen_semanal = []
        for unidad, df_u in df.groupby("Agrupación"):
            dias_operados = df_u["Fecha"].dropna().nunique()
            if dias_operados == 0:
                dias_operados = 1

            vueltas_totales = (
                df_u.groupby("Fecha")["Vuelta_Num"].max().sum()
                if "Vuelta_Num" in df_u.columns
                else 1
            )

            cortes_totales = df_u["Estado_Ruta"].astype(str).str.contains("CORTE").sum()
            omitidas_totales = (
                df_u["Tipo"].astype(str).str.contains("Omitida").sum()
                + df_u["Estado_Ruta"].astype(str).str.contains("NO REGISTRADA").sum()
            )

            resumen_semanal.append(
                {
                    "Unidad": unidad,
                    "Dias_Trabajados": int(dias_operados),
                    "Vueltas_Semanales": int(vueltas_totales),
                    "Cortes_Ruta": int(cortes_totales),
                    "Geocercas_Omitidas": int(omitidas_totales),
                }
            )

        return pd.DataFrame(resumen_semanal)