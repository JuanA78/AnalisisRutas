import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from configuracion.colores import PaletaColores


class GraficoPaiUnidades(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="Main.TFrame")

        # ------------------------------------------------------------
        # 1. PANEL SUPERIOR: ÁREA DE SCROLL CON LAS GRÁFICAS
        # ------------------------------------------------------------
        self.container_graficas = tk.Frame(self, bg="#FFFFFF")
        self.container_graficas.pack(side="top", fill="both", expand=True)

        self.canvas_scroll = tk.Canvas(self.container_graficas, bg="#FFFFFF", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.container_graficas, orient="vertical", command=self.canvas_scroll.yview)
        self.scroll_frame = tk.Frame(self.canvas_scroll, bg="#FFFFFF")

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas_scroll.configure(scrollregion=self.canvas_scroll.bbox("all"))
        )

        self.canvas_scroll.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas_scroll.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas_scroll.pack(side="left", fill="both", expand=True)

        self.canvas_scroll.bind_all("<MouseWheel>", self._al_hacer_scroll)

        # ------------------------------------------------------------
        # 2. PANEL INFERIOR MODERNO: TARJETA DE DETALLE
        # ------------------------------------------------------------
        self.panel_detalle = tk.Frame(self, bg="#0F172A", bd=0, padx=15, pady=10)
        self.panel_detalle.pack(side="bottom", fill="x")

        # Encabezado del panel
        self.lbl_titulo_detalle = tk.Label(
            self.panel_detalle,
            text="📌 DETALLE INTERACTIVO DE UNIDAD",
            bg="#0F172A", fg="#38BDF8",
            font=("Segoe UI", 11, "bold")
        )
        self.lbl_titulo_detalle.pack(anchor="w")

        # Texto del detalle (font size cambiado de 9.5 a 9 entero)
        self.lbl_contenido_detalle = tk.Label(
            self.panel_detalle,
            text="Haz clic sobre cualquier rebanada del gráfico (Omisión, Retraso, Adelanto, etc.) para consultar aquí el desglose completo.",
            bg="#0F172A", fg="#CBD5E1",
            font=("Segoe UI", 9), justify="left", wraplength=1200
        )
        self.lbl_contenido_detalle.pack(anchor="w", pady=(4, 2))

    def _al_hacer_scroll(self, event):
        self.canvas_scroll.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def renderizar_pie_charts(self, df_resultado: pd.DataFrame):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if df_resultado is None or df_resultado.empty:
            lbl_empty = tk.Label(
                self.scroll_frame,
                text="No hay datos cargados para generar estadísticas.",
                bg="#FFFFFF",
                fg=getattr(PaletaColores, "TEXTO_OSCURO", "#0F172A"),
                font=("Segoe UI", 10, "bold")
            )
            lbl_empty.pack(padx=20, pady=20)
            return

        col_unidad = next((c for c in df_resultado.columns if "AGRUPA" in c.upper() or "UNIDAD" in c.upper()), None)
        if not col_unidad:
            return

        unidades = sorted(df_resultado[col_unidad].astype(str).unique().tolist())
        COLUMNAS_POR_FILA = 3

        for i, unidad_id in enumerate(unidades):
            df_u = df_resultado[df_resultado[col_unidad].astype(str) == unidad_id]
            
            fila = i // COLUMNAS_POR_FILA
            columna = i % COLUMNAS_POR_FILA

            frame_card = tk.Frame(self.scroll_frame, bg="#FFFFFF", bd=1, relief="solid")
            frame_card.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")

            self._crear_figura_y_vincular_clic(frame_card, df_u, unidad_id)

        for col in range(COLUMNAS_POR_FILA):
            self.scroll_frame.columnconfigure(col, weight=1)

    generar_graficas_unidades = renderizar_pie_charts

    def _crear_figura_y_vincular_clic(self, container: tk.Widget, df_u: pd.DataFrame, unidad_id: str):
        fig, ax = plt.subplots(figsize=(3.6, 3.2), dpi=95, facecolor="#FFFFFF")
        ax.set_facecolor("#FFFFFF")

        conteos = {
            "A Tiempo": 0,
            "Adelanto": 0,
            "Retraso": 0,
            "Omisión": 0,
            "Corte Ruta": 0
        }

        geocercas_omitidas = {}
        total_segs_retraso = 0.0

        for _, r in df_u.iterrows():
            eval_t = str(r.get("Evaluacion_Tiempo", ""))
            estado = str(r.get("Estado_Ruta", ""))
            tipo = str(r.get("Tipo", ""))
            geo = str(r.get("Geocerca", ""))
            segs_ret = r.get("Segundos_Retraso", 0.0)

            if isinstance(segs_ret, (int, float)) and segs_ret > 0:
                total_segs_retraso += segs_ret

            if "NO REGISTRADA" in estado or "Omitida" in tipo or "Faltante" in geo:
                conteos["Omisión"] += 1
                geo_limpia = geo.replace("(Faltante)", "").strip()
                geocercas_omitidas[geo_limpia] = geocercas_omitidas.get(geo_limpia, 0) + 1
            elif "CORTE" in estado or "Corte" in tipo:
                conteos["Corte Ruta"] += 1
            elif "Retraso" in eval_t:
                conteos["Retraso"] += 1
            elif "Adelanto" in eval_t:
                conteos["Adelanto"] += 1
            elif "A Tiempo" in eval_t:
                conteos["A Tiempo"] += 1

        labels, sizes, colors = [], [], []
        mapa_colores = {
            "A Tiempo": "#10B981",
            "Adelanto": "#F97316",
            "Retraso": "#EF4444",
            "Omisión": "#2563EB",
            "Corte Ruta": "#8B5CF6"
        }

        total_eventos = sum(conteos.values())
        wedges = []

        if total_eventos > 0:
            for cat, count in conteos.items():
                if count > 0:
                    labels.append(cat)
                    sizes.append(count)
                    colors.append(mapa_colores[cat])

            wedges, _, _ = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",
                startangle=140,
                textprops={"fontsize": 8, "fontweight": "bold", "color": "#1E293B"},
                wedgeprops={"edgecolor": "#FFFFFF", "linewidth": 1.5}
            )

        ax.set_title(f"UNIDAD: {unidad_id}", color="#0F172A", fontsize=10, fontweight="bold", pad=8)
        plt.tight_layout()

        canvas_fig = FigureCanvasTkAgg(fig, master=container)
        canvas_widget = canvas_fig.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=5, pady=5)
        canvas_fig.draw()

        def procesar_clic_tk(event):
            for i, w in enumerate(wedges):
                if w.contains_point((event.x, canvas_widget.winfo_height() - event.y)):
                    cat_label = labels[i]
                    
                    self.lbl_titulo_detalle.config(
                        text=f"📌 UNIDAD {unidad_id} — DETALLE DE {cat_label.upper()}",
                        fg=mapa_colores.get(cat_label, "#38BDF8")
                    )

                    if cat_label == "Omisión":
                        detalles_om = [f"• {g}: {cant} vez(ces)" for g, cant in geocercas_omitidas.items()]
                        texto = f"Total de Omisiones: {conteos['Omisión']}  |  Geocercas no registradas: " + (",  ".join(detalles_om) if detalles_om else "Sin registros específicos.")
                    elif cat_label == "Retraso":
                        mins_tot = round(total_segs_retraso / 60.0, 1)
                        texto = f"Total de Retrasos: {conteos['Retraso']} eventos.  |  Tiempo total acumulado en retrasos: +{mins_tot} minutos de desfase."
                    else:
                        texto = f"Categoría: {cat_label}  |  Total de eventos registrados: {sizes[i]}"

                    self.lbl_contenido_detalle.config(text=texto)
                    return

        canvas_widget.bind("<Button-1>", procesar_clic_tk)