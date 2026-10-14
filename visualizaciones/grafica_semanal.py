# visualizaciones/grafica_semanal.py
import matplotlib.pyplot as plt
import pandas as pd
from configuracion.colores import PaletaColores


class GraficaSemanalBuilder:

    @staticmethod
    def calcular_metricas_semanales_reales(df_u: pd.DataFrame):
        """Calcula de forma exacta las vueltas por día y las métricas semanales reales."""
        if df_u is None or df_u.empty:
            return {
                "vueltas_totales": 0,
                "dias_trabajados": 0,
                "promedio_diario": 0,
                "saltadas": 0,
                "cortes": 0,
                "reinicios": 0,
                "df_desglose_dias": pd.DataFrame(),
            }

        df = df_u.copy()

        # Parsear fecha
        if "Hora de salida" in df.columns and hasattr(df["Hora de salida"], "dt"):
            df["Fecha_Dia"] = df["Hora de salida"].dt.date
        elif "Hora de salida" in df.columns:
            df["Fecha_Dia"] = pd.to_datetime(
                df["Hora de salida"], dayfirst=True, errors="coerce"
            ).dt.date
        else:
            df["Fecha_Dia"] = "Día Operativo"

        desglose = []
        vueltas_totales_semana = 0

        # Iterar día por día para calcular el verdadero total de vueltas de cada día
        for fecha, df_dia in df.groupby("Fecha_Dia"):
            if pd.isna(fecha):
                continue

            v_min = df_dia["Vuelta_Num"].min() if "Vuelta_Num" in df_dia.columns else 1
            v_max = df_dia["Vuelta_Num"].max() if "Vuelta_Num" in df_dia.columns else 1
            
            # Vueltas reales del día = Max - Min + 1
            vueltas_dia = max(1, int(v_max - v_min + 1)) if len(df_dia) > 1 else 1
            vueltas_totales_semana += vueltas_dia

            c_cortes = df_dia["Estado_Ruta"].astype(str).str.contains("CORTE").sum()
            c_reinicios = df_dia["Estado_Ruta"].astype(str).str.contains("Reinicio").sum()
            c_omitidas = (
                (df_dia["Tipo"].astype(str) == "Omitida")
                | (df_dia["Estado_Ruta"].astype(str).str.contains("NO REGISTRADA"))
            ).sum()

            desglose.append(
                {
                    "Fecha": str(fecha),
                    "Vueltas": vueltas_dia,
                    "Omitidas": c_omitidas,
                    "Cortes": c_cortes,
                    "Reinicios": c_reinicios,
                }
            )

        df_desglose = pd.DataFrame(desglose)
        dias_trabajados = len(df_desglose) if not df_desglose.empty else 1
        promedio_diario = round(vueltas_totales_semana / dias_trabajados, 1)

        cortes_totales = df["Estado_Ruta"].astype(str).str.contains("CORTE").sum()
        reinicios_totales = df["Estado_Ruta"].astype(str).str.contains("Reinicio").sum()
        omitidas_totales = (
            (df["Tipo"].astype(str) == "Omitida")
            | (df["Estado_Ruta"].astype(str).str.contains("NO REGISTRADA"))
        ).sum()

        return {
            "vueltas_totales": vueltas_totales_semana,
            "dias_trabajados": dias_trabajados,
            "promedio_diario": promedio_diario,
            "saltadas": omitidas_totales,
            "cortes": cortes_totales,
            "reinicios": reinicios_totales,
            "df_desglose_dias": df_desglose,
        }

    @staticmethod
    def crear_dashboard_semanal_unidad(df_u: pd.DataFrame, unidad_id: str) -> plt.Figure:
        plt.close("all")
        fig, ax = plt.subplots(
            figsize=(10.5, 3.8), dpi=95, facecolor=PaletaColores.PANEL_LATERAL
        )
        ax.set_facecolor(PaletaColores.CARD_BG)

        if df_u is None or df_u.empty:
            ax.text(
                0.5, 0.5, "Sin Registros Semanales",
                color=PaletaColores.TEXTO_MUTED, ha="center", va="center", fontsize=11
            )
            return fig

        metricas = GraficaSemanalBuilder.calcular_metricas_semanales_reales(df_u)
        correctos = max(0, len(df_u) - metricas["cortes"] - metricas["saltadas"])

        categorias = ["Cumplidas / A Tiempo", "Cortes de Ruta", "Geocercas Omitidas"]
        valores = [correctos, metricas["cortes"], metricas["saltadas"]]
        colores = [PaletaColores.VERDE_EXITO, PaletaColores.PURPURA_REINICIO, PaletaColores.ROJO_ALERTA]

        cat_filt = [c for c, v in zip(categorias, valores) if v > 0]
        val_filt = [v for v in valores if v > 0]
        col_filt = [c for c, v in zip(colores, valores) if v > 0]

        if val_filt:
            wedges, texts, autotexts = ax.pie(
                val_filt,
                labels=cat_filt,
                autopct="%1.1f%%",
                pctdistance=0.75,
                startangle=140,
                colors=col_filt,
                textprops=dict(color=PaletaColores.TEXTO_BLANCO, fontsize=9, fontweight="bold"),
                wedgeprops=dict(width=0.45, edgecolor=PaletaColores.PANEL_LATERAL, linewidth=2),
            )
            for at in autotexts:
                at.set_color("#FFFFFF")
                at.set_fontsize(10)
        else:
            ax.text(
                0, 0, "Sin Registros Suficientes",
                color=PaletaColores.TEXTO_MUTED, ha="center", va="center", fontsize=10
            )

        ax.set_title(
            f"CUMPLIMIENTO OPERACIONAL SEMANAL — UNIDAD {unidad_id}",
            color=PaletaColores.CELESTE_VIBRANTE,
            fontsize=11,
            fontweight="bold",
            pad=12,
        )

        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.tight_layout()
        return fig