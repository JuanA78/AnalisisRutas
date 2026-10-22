import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

from configuracion.colores import PaletaColores
from configuracion.rutas_config import RutasConfig


class GraficaTrazoRecorrido:

    @classmethod
    def crear_grafica_trayectoria(
        cls,
        df_u: pd.DataFrame,
        ruta_seleccionada: str = None
    ) -> plt.Figure:

        plt.close("all")

        fig, ax = plt.subplots(
            figsize=(11, 5),
            dpi=95,
            facecolor=PaletaColores.PANEL_LATERAL
        )

        ax.set_facecolor(PaletaColores.CARD_BG)

        if df_u is None or df_u.empty:
            return fig

        # 1. Identificar unidad y ruta
        col_unid = (
            "Agrupación"
            if "Agrupación" in df_u.columns
            else df_u.columns[0]
        )

        unidad_id = str(df_u[col_unid].iloc[0]).strip().upper()

        ruta_cat = RutasConfig.obtener_ruta_predeterminada(unidad_id)

        if ruta_seleccionada:
            es_agua_salada = "AGUA SALADA" in ruta_seleccionada.upper()
        elif ruta_cat == "El Arbolito":
            es_agua_salada = False
        elif ruta_cat == "Agua Salada":
            es_agua_salada = True
        elif "Geocerca" in df_u.columns:
            geocercas_unidad = (
                df_u["Geocerca"]
                .astype(str)
                .str.replace(" (Faltante)", "", regex=False)
                .str.strip()
                .unique()
            )

            es_agua_salada = any(
                g in ["Canal_CasaEloy", "AguaSalada"]
                for g in geocercas_unidad
            )
        else:
            es_agua_salada = False

        # 2. Eje X de acuerdo con la ruta seleccionada
        eje_geocercas = (
            RutasConfig.EJE_X_AGUA_SALADA
            if es_agua_salada
            else RutasConfig.EJE_X_EL_ARBOLITO
        )

        x_map = {
            geocerca: i
            for i, geocerca in enumerate(eje_geocercas)
        }

        # 3. Extraer puntos válidos
        puntos = cls._extraer_puntos(df_u, x_map)

        # 4. Dibujar trayectoria completa y marcadores
        cls._trazar_lineas_y_puntos(ax, puntos)

        # 5. Configurar ejes
        ax.set_xticks(range(len(eje_geocercas)))

        ax.set_xticklabels(
            eje_geocercas,
            fontsize=8.5,
            fontweight="bold",
            color=PaletaColores.TEXTO_BLANCO,
            rotation=12
        )

        ax.set_ylabel(
            "Nº de Vuelta",
            fontsize=9.5,
            fontweight="bold",
            color=PaletaColores.TEXTO_MUTED
        )

        titulo_ruta = (
            "AGUA SALADA"
            if es_agua_salada
            else "EL ARBOLITO"
        )

        ax.set_title(
            f"TRAYECTORIA CONTINUA — UNIDAD {unidad_id} [{titulo_ruta}]",
            color=PaletaColores.CELESTE_VIBRANTE,
            fontsize=10,
            fontweight="bold",
            pad=10
        )

        cls._aplicar_estilo_y_leyenda(ax, puntos)

        # 6. Tooltip interactivo
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 30),
            textcoords="offset points",
            bbox=dict(
                boxstyle="round,pad=0.6",
                fc="#0B132B",
                ec="#38BDF8",
                lw=1.5
            ),
            arrowprops=dict(
                arrowstyle="->",
                connectionstyle="arc3,rad=0",
                color="#38BDF8",
                lw=1.2
            ),
            color="#FFFFFF",
            fontsize=8,
            fontfamily="Consolas",
            ha="center",
            zorder=1000
        )

        annot.set_visible(False)

        def hover(event):
            if event.inaxes != ax:
                if annot.get_visible():
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
                return

            if event.xdata is None or event.ydata is None:
                return

            for p in puntos:
                if (
                    abs(event.xdata - p["x"]) < 0.25
                    and abs(event.ydata - p["y"]) < 0.25
                ):
                    annot.xy = (p["x"], p["y"])

                    texto = (
                        f"GEOCERCA: {p['geocerca_nombre']}\n"
                        f"Vuelta: {p['vuelta_base']} | Sentido: {p['sentido']}\n"
                        f"Entrada: {p['entrada']} | Salida: {p['salida']}\n"
                        f"Tiempo Real: {p['tiempo_real']} | "
                        f"Estimado: {p['tiempo_est']}\n"
                        f"Desfase: {p['desfase']} ({p['evaluacion']})\n"
                        f"Estado: {p['estado']}"
                    )

                    annot.set_text(texto)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return

            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

        plt.tight_layout()

        return fig

    @staticmethod
    def _extraer_puntos(
        df_u: pd.DataFrame,
        x_map: dict
    ) -> list:

        puntos = []

        for _, r in df_u.iterrows():

            tipo_r = str(r.get("Tipo", "")).strip().upper()
            estado_r = str(r.get("Estado_Ruta", "")).strip().upper()

            # Omitir geocercas repetidas en el gráfico
            if (
                "REPETIDA" in tipo_r
                or "GEOCERCA REPETIDA" in estado_r
            ):
                continue

            val_g = str(r.get("Geocerca", "")).strip()
            eval_t = str(r.get("Evaluacion_Tiempo", ""))
            desfase = str(r.get("Desfase", "-"))

            # Identificar eventos
            es_faltante = (
                "FALTANTE" in val_g.upper()
                or "NO REGISTRADA" in estado_r
                or "OMITIDA" in tipo_r
            )

            es_corte = (
                "CORTE" in estado_r
                or "CORTE" in tipo_r
            )

            es_anomalia = (
                "ANOMALÍA" in estado_r
                or "ANOMALIA" in estado_r
                or "ANOMALÍA" in tipo_r
                or "ANOMALIA" in tipo_r
                or "REINICIO" in estado_r
                or "REINICIO" in tipo_r
            )

            es_inicio = (
                "INICIO DE RUTA" in estado_r
                or "INICIO DE RUTA" in tipo_r
            )

            g_nombre = val_g.replace(" (Faltante)", "").strip()

            if g_nombre not in x_map:
                continue

            try:
                vuelta_base = int(float(r.get("Vuelta_Num", 1)))
            except (ValueError, TypeError):
                vuelta_base = 1

            sentido = str(r.get("Sentido", "Ida")).strip()

            # Separar visualmente ida (-0.20) y regreso (+0.20)
            y_offset = (
                -0.20
                if sentido.lower() == "ida"
                else 0.20
            )

            x_pos = float(x_map[g_nombre])
            y_pos = float(vuelta_base) + y_offset

            # Colores de evaluación
            if es_faltante:
                color = PaletaColores.ROJO_ALERTA
            elif es_anomalia:
                color = "#8B5CF6"  # Púrpura para anomalías
            elif "RETRASO" in eval_t.upper() or desfase.startswith("+"):
                color = PaletaColores.ROJO_ALERTA
            elif "ADELANTO" in eval_t.upper() or ("-" in desfase and desfase != "-"):
                color = "#F97316"
            else:
                color = PaletaColores.VERDE_EXITO

            puntos.append({
                "x": x_pos,
                "y": y_pos,
                "vuelta_base": vuelta_base,
                "sentido": sentido,
                "color": color,
                "es_faltante": es_faltante,
                "es_corte": es_corte,
                "es_anomalia": es_anomalia,
                "es_inicio": es_inicio,
                "geocerca_nombre": g_nombre,
                "entrada": str(r.get("Entrada", "-")),
                "salida": str(r.get("Salida", "-")),
                "tiempo_real": str(r.get("Tiempo_Real", "-")),
                "tiempo_est": str(r.get("Tiempo_Estimado", "-")),
                "desfase": desfase,
                "evaluacion": eval_t,
                "estado": estado_r
            })

        return puntos

    @staticmethod
    def _trazar_lineas_y_puntos(ax, puntos: list):

        if not puntos:
            return

        # 1. Conectar cada punto con el siguiente
        for i in range(len(puntos) - 1):

            p1 = puntos[i]
            p2 = puntos[i + 1]

            es_transicion = (
                p1["vuelta_base"] != p2["vuelta_base"]
                or p1["es_inicio"]
                or p2["es_inicio"]
                or p1["es_anomalia"]
                or p2["es_anomalia"]
            )

            if es_transicion:
                color_linea = "#9CA3AF"
                estilo_linea = ":"
                grosor = 1.8

            else:
                es_ida = p1["sentido"].lower() == "ida"

                color_linea = (
                    PaletaColores.TEXTO_BLANCO
                    if es_ida
                    else PaletaColores.CELESTE_VIBRANTE
                )

                estilo_linea = "-" if es_ida else "--"
                grosor = 2.3

            ax.plot(
                [p1["x"], p2["x"]],
                [p1["y"], p2["y"]],
                color=color_linea,
                linestyle=estilo_linea,
                linewidth=grosor,
                alpha=0.95,
                zorder=2
            )

        # 2. Dibujar marcadores según el estado
        for p in puntos:

            if p["es_faltante"]:
                # X roja para indicar omitidas
                ax.scatter(
                    p["x"],
                    p["y"],
                    color=PaletaColores.ROJO_ALERTA,
                    marker="x",
                    linewidths=3,
                    s=120,
                    zorder=6
                )

            elif p["es_anomalia"]:
                # Diamante morado para anomalías
                ax.scatter(
                    p["x"],
                    p["y"],
                    color="#8B5CF6",
                    edgecolors="#FFFFFF",
                    linewidths=1.2,
                    marker="D",
                    s=75,
                    zorder=6
                )

            else:
                # Círculos normales para puntos A Tiempo / Adelanto / Retraso / Corte
                ax.scatter(
                    p["x"],
                    p["y"],
                    color=p["color"],
                    edgecolors="#FFFFFF",
                    linewidths=1.1,
                    marker="o",
                    s=65,
                    zorder=5
                )

    @staticmethod
    def _aplicar_estilo_y_leyenda(ax, puntos: list):

        vueltas = sorted({
            p["vuelta_base"]
            for p in puntos
            if p.get("vuelta_base") is not None
        }) if puntos else [1]

        if not vueltas:
            vueltas = [1]

        min_v = min(vueltas)
        max_v = max(vueltas)

        ax.set_ylim(min_v - 0.6, max_v + 0.6)
        ax.set_yticks(vueltas)
        ax.set_yticklabels([f"Vuelta {v}" for v in vueltas], fontsize=8.5, fontweight="bold")

        ax.tick_params(colors=PaletaColores.TEXTO_MUTED)

        ax.grid(
            True,
            linestyle="--",
            alpha=0.15,
            color="#FFFFFF"
        )

        for spine in ax.spines.values():
            spine.set_visible(False)

        # Leyenda
        elementos = [
            Line2D([0], [0], color=PaletaColores.TEXTO_BLANCO, lw=2.5, linestyle="-", label="Trayecto IDA"),
            Line2D([0], [0], color=PaletaColores.CELESTE_VIBRANTE, lw=2.5, linestyle="--", label="Trayecto REGRESO"),
            Line2D([0], [0], color="#9CA3AF", lw=1.8, linestyle=":", label="Inicio / Cambio de vuelta"),
            Line2D([0], [0], marker="o", color="w", linestyle="None", markerfacecolor=PaletaColores.VERDE_EXITO, markersize=7, label="A Tiempo"),
            Line2D([0], [0], marker="o", color="w", linestyle="None", markerfacecolor="#F97316", markersize=7, label="Adelanto"),
            Line2D([0], [0], marker="o", color="w", linestyle="None", markerfacecolor=PaletaColores.ROJO_ALERTA, markersize=7, label="Retraso"),
            Line2D([0], [0], marker="D", color="w", linestyle="None", markerfacecolor="#8B5CF6", markersize=7, label="Anomalía de Ruta"),
            Line2D([0], [0], marker="x", color=PaletaColores.ROJO_ALERTA, linestyle="None", markersize=8, markeredgewidth=2, label="Geocerca Omitida")
        ]

        ax.legend(
            handles=elementos,
            loc="upper right",
            frameon=True,
            facecolor=PaletaColores.CARD_OSCURA,
            edgecolor="none",
            labelcolor=PaletaColores.TEXTO_BLANCO,
            fontsize=7.5
        )