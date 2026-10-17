import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
from configuracion.colores import PaletaColores
from configuracion.rutas_config import RutasConfig


class GraficaTrazoRecorrido:

    @classmethod
    def crear_grafica_trayectoria(cls, df_u: pd.DataFrame, ruta_seleccionada: str = None) -> plt.Figure:
        plt.close("all")
        fig, ax = plt.subplots(figsize=(11, 5), dpi=95, facecolor=PaletaColores.PANEL_LATERAL)
        ax.set_facecolor(PaletaColores.CARD_BG)

        if df_u is None or df_u.empty:
            return fig

        # 1. Identificar Unidad y Ruta
        col_unid = "Agrupación" if "Agrupación" in df_u.columns else df_u.columns[0]
        unidad_id = str(df_u[col_unid].iloc[0]).strip().upper()

        ruta_cat = RutasConfig.obtener_ruta_predeterminada(unidad_id)
        
        if ruta_cat == "El Arbolito":
            es_agua_salada = False
        elif ruta_cat == "Agua Salada":
            es_agua_salada = True
        else:
            geocercas_unidad = (
                df_u["Geocerca"]
                .astype(str)
                .str.replace(" (Faltante)", "", regex=False)
                .str.strip()
                .unique()
            )
            es_agua_salada = any(g in ["Canal_CasaEloy", "AguaSalada"] for g in geocercas_unidad)

        # 2. Eje X ordenado de geocercas
        eje_geocercas = (
            RutasConfig.EJE_X_AGUA_SALADA
            if es_agua_salada
            else RutasConfig.EJE_X_EL_ARBOLITO
        )
        x_map = {g: i for i, g in enumerate(eje_geocercas)}

        # 3. Extraer Puntos de la Unidad
        puntos = cls._extraer_puntos(df_u, x_map)
        cls._trazar_lineas_y_puntos(ax, puntos)

        # 4. Configurar Ejes y Títulos
        ax.set_xticks(range(len(eje_geocercas)))
        ax.set_xticklabels(
            eje_geocercas,
            fontsize=8.5,
            fontweight="bold",
            color=PaletaColores.TEXTO_BLANCO,
            rotation=12,
        )
        ax.set_ylabel("Nº de Vuelta", fontsize=9.5, fontweight="bold", color=PaletaColores.TEXTO_MUTED)
        
        titulo_ruta = "AGUA SALADA" if es_agua_salada else "EL ARBOLITO"
        ax.set_title(
            f"TRAYECTORIA CONTINUA — UNIDAD {unidad_id} [{titulo_ruta}]",
            color=PaletaColores.CELESTE_VIBRANTE,
            fontsize=10,
            fontweight="bold",
            pad=10,
        )

        cls._aplicar_estilo_y_leyenda(ax, puntos)

        # 5. Tooltip por encima de todas las capas (zorder=1000)
        annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(0, 30),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.6", fc="#0B132B", ec="#38BDF8", lw=1.5),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color="#38BDF8", lw=1.2),
            color="#FFFFFF",
            fontsize=8,
            fontfamily="Consolas",
            ha="center",
            zorder=1000  # Forzar despliegue al frente
        )
        annot.set_visible(False)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for p in puntos:
                    cont = (abs(event.xdata - p["x"]) < 0.25) and (abs(event.ydata - p["y"]) < 0.25) if event.xdata and event.ydata else False
                    if cont:
                        annot.xy = (p["x"], p["y"])
                        texto = (
                            f"GEOCERCA: {p['geocerca_nombre']}\n"
                            f"Entrada: {p['entrada']} | Salida: {p['salida']}\n"
                            f"Tiempo Real: {p['tiempo_real']} | Estimado: {p['tiempo_est']}\n"
                            f"Desfase: {p['desfase']} ({p['evaluacion']})\n"
                            f"Estado: {p['estado']}"
                        )
                        annot.set_text(texto)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)

        plt.tight_layout()
        return fig

    @staticmethod
    def _extraer_puntos(df_u: pd.DataFrame, x_map: dict) -> list:
        puntos = []
        for _, r in df_u.iterrows():
            val_g = str(r.get("Geocerca", "")).strip()
            estado_r = str(r.get("Estado_Ruta", ""))
            tipo_r = str(r.get("Tipo", ""))
            eval_t = str(r.get("Evaluacion_Tiempo", ""))

            es_faltante = "Faltante" in val_g or "NO REGISTRADA" in estado_r or "Omitida" in tipo_r
            g_nombre = val_g.replace(" (Faltante)", "").strip()

            if g_nombre in x_map:
                vuelta_base = float(r.get("Vuelta_Num", 1))
                sentido = str(r.get("Sentido", "Ida"))

                y_offset = -0.20 if sentido == "Ida" else 0.20
                y_pos = vuelta_base + y_offset

                desfase = str(r.get("Desfase", "-"))
                
                # Colores según tipo de evento
                if es_faltante:
                    col = PaletaColores.ROJO_ALERTA
                elif "Reinicio" in estado_r or "CORTE" in estado_r or "Corte" in tipo_r:
                    col = "#8B5CF6"
                elif "Retraso" in eval_t or "+" in desfase:
                    col = PaletaColores.ROJO_ALERTA
                elif "Adelanto" in eval_t or ("-" in desfase and desfase != "-"):
                    col = "#F97316"
                else:
                    col = PaletaColores.VERDE_EXITO

                puntos.append(
                    {
                        "x": x_map[g_nombre],
                        "y": y_pos,
                        "vuelta_base": int(vuelta_base),
                        "sentido": sentido,
                        "color": col,
                        "es_faltante": es_faltante,
                        "es_reinicio": "Reinicio" in estado_r or "CORTE" in estado_r,
                        "geocerca_nombre": g_nombre,
                        "entrada": str(r.get("Entrada", "-")),
                        "salida": str(r.get("Salida", "-")),
                        "tiempo_real": str(r.get("Tiempo_Real", "-")),
                        "tiempo_est": str(r.get("Tiempo_Estimado", "-")),
                        "desfase": desfase,
                        "evaluacion": eval_t if eval_t else "Normal",
                        "estado": estado_r if estado_r else "OK",
                    }
                )
        return puntos

    @staticmethod
    def _trazar_lineas_y_puntos(ax, puntos: list):
        for i in range(len(puntos) - 1):
            p1, p2 = puntos[i], puntos[i + 1]
            
            # 1. Si es un Corte o Reinicio real explicitado
            if p2["es_reinicio"]:
                ax.plot(
                    [p1["x"], p2["x"]],
                    [p1["y"], p2["y"]],
                    color="#8B5CF6",
                    linestyle=":",
                    linewidth=2.2,
                    alpha=0.9,
                    zorder=1
                )
            # 2. Si cambia de vuelta (transición terminal)
            elif p1["vuelta_base"] != p2["vuelta_base"]:
                ax.plot(
                    [p1["x"], p2["x"]],
                    [p1["y"], p2["y"]],
                    color=PaletaColores.TEXTO_MUTED,
                    linestyle=":",
                    linewidth=1.5,
                    alpha=0.6,
                    zorder=1
                )
            # 3. Trayecto normal de la misma vuelta (incluso si se omitieron geocercas intermedias)
            else:
                col_linea = PaletaColores.TEXTO_BLANCO if p1["sentido"] == "Ida" else PaletaColores.CELESTE_VIBRANTE
                style_linea = "-" if p1["sentido"] == "Ida" else "--"
                ax.plot(
                    [p1["x"], p2["x"]],
                    [p1["y"], p2["y"]],
                    color=col_linea,
                    linestyle=style_linea,
                    linewidth=2.3,
                    alpha=0.9,
                    zorder=2
                )

        # Dibujar puntos y taches sobre las líneas
        for p in puntos:
            if p["es_faltante"]:
                ax.scatter(p["x"], p["y"], color=PaletaColores.ROJO_ALERTA, marker="x", linewidth=3.5, s=140, zorder=5)
            else:
                ax.scatter(p["x"], p["y"], color=p["color"], edgecolors="#FFFFFF", linewidth=1.2, s=80, zorder=4)

    @staticmethod
    def _aplicar_estilo_y_leyenda(ax, puntos: list):
        vueltas_base_unicas = sorted(list(set([p["vuelta_base"] for p in puntos]))) if puntos else [1]
        ax.set_ylim(min(vueltas_base_unicas) - 0.6, max(vueltas_base_unicas) + 0.6)
        ax.set_yticks(vueltas_base_unicas)

        ax.tick_params(colors=PaletaColores.TEXTO_MUTED)
        ax.grid(True, linestyle="--", alpha=0.15, color="#FFFFFF")
        for spine in ax.spines.values():
            spine.set_visible(False)

        legend_elements = [
            Line2D([0], [0], color=PaletaColores.TEXTO_BLANCO, lw=2.5, label="Trayecto IDA (Continua)"),
            Line2D([0], [0], color=PaletaColores.CELESTE_VIBRANTE, lw=2.5, linestyle="--", label="Trayecto REGRESO (Punteada)"),
            Line2D([0], [0], color="#8B5CF6", lw=2, linestyle=":", label="Reinicio / Corte de Ruta"),
            Line2D([0], [0], marker="o", color="w", label="A Tiempo", markerfacecolor=PaletaColores.VERDE_EXITO, markersize=7),
            Line2D([0], [0], marker="o", color="w", label="Adelanto", markerfacecolor="#F97316", markersize=7),
            Line2D([0], [0], marker="o", color="w", label="Retraso", markerfacecolor=PaletaColores.ROJO_ALERTA, markersize=7),
            Line2D([0], [0], marker="x", color=PaletaColores.ROJO_ALERTA, label="Geocerca Omitida", markersize=7, lw=2),
        ]
        ax.legend(
            handles=legend_elements,
            loc="upper right",
            frameon=True,
            facecolor=PaletaColores.CARD_OSCURA,
            edgecolor="none",
            labelcolor=PaletaColores.TEXTO_BLANCO,
            fontsize=7.5,
        )