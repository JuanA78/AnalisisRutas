# interfaz/vista_grafica_individual.py
import tkinter as tk
from tkinter import ttk
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from configuracion.colores import PaletaColores
from visualizaciones.grafica_diaria import GraficaDiariaBuilder
from visualizaciones.grafica_semanal import GraficaSemanalBuilder


class VistaGraficaIndividual(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.df_resultado = None
        self.canvas_diaria = None
        self.toolbar_diaria = None
        self.es_semanal = False

        self.configure(style="Main.TFrame")
        self._crear_layout()

    def _crear_layout(self):
        frame_top_d = tk.Frame(self, bg=PaletaColores.PANEL_LATERAL, padx=12, pady=8)
        frame_top_d.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            frame_top_d,
            text="Seleccionar Unidad para Reporte:",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.cb_unidades = ttk.Combobox(
            frame_top_d, state="readonly", width=22, font=("Segoe UI", 10)
        )
        self.cb_unidades.pack(side="left")
        self.cb_unidades.bind("<<ComboboxSelected>>", self._al_seleccionar_unidad)

        # BOTÓN MAXIMIZAR RESTAURADO
        btn_max = tk.Button(
            frame_top_d,
            text="🔍 Maximizar Gráfica",
            bg=PaletaColores.AZUL_OCEANO,
            fg="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            command=self._maximizar_grafica,
        )
        btn_max.pack(side="right", padx=(10, 0))

        self.lbl_modo_reporte = tk.Label(
            frame_top_d,
            text="MODO: DIARIO",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.VERDE_EXITO,
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_modo_reporte.pack(side="right", padx=10)

        # CARDS KPI SUPERIORES
        frame_cards = tk.Frame(self, bg=PaletaColores.PANEL_LATERAL, padx=10, pady=8)
        frame_cards.pack(fill="x", padx=10, pady=(0, 5))

        grid_cards = tk.Frame(frame_cards, bg=PaletaColores.PANEL_LATERAL)
        grid_cards.pack(fill="x", expand=True)

        self.card_title_1, self.lbl_card_1 = self._crear_card_kpi(grid_cards, "HORA INICIO", "--:--:--", 0)
        self.card_title_2, self.lbl_card_2 = self._crear_card_kpi(grid_cards, "HORA TERMINO", "--:--:--", 1)
        self.card_title_3, self.lbl_card_3 = self._crear_card_kpi(grid_cards, "GEOCERCA INICIO", "-", 2, color_val=PaletaColores.CELESTE_VIBRANTE)
        self.card_title_4, self.lbl_card_4 = self._crear_card_kpi(grid_cards, "VUELTAS TOTALES", "0", 3, color_val=PaletaColores.VERDE_EXITO)
        self.card_title_5, self.lbl_card_5 = self._crear_card_kpi(grid_cards, "REINICIOS / CORTES", "0", 4, color_val=PaletaColores.PURPURA_REINICIO)
        self.card_title_6, self.lbl_card_6 = self._crear_card_kpi(grid_cards, "MAXIMO RETRASO", "-", 5, color_val=PaletaColores.ROJO_ALERTA)

        self.frame_contenido = tk.Frame(self, bg=PaletaColores.BG_PRINCIPAL)
        self.frame_contenido.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.frame_grafico = tk.Frame(self.frame_contenido, bg=PaletaColores.BG_PRINCIPAL)
        self.frame_grafico.pack(fill="both", expand=True)

        # TABLA DE DESGLOSE SEMANAL
        self.frame_tabla_dias = tk.Frame(self.frame_contenido, bg=PaletaColores.PANEL_LATERAL, padx=10, pady=6)

        tk.Label(
            self.frame_tabla_dias,
            text="📅 DESGLOSE DETALLADO POR DÍAS TRABAJADOS EN LA SEMANA",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        cols_dias = ("Fecha", "Vueltas", "Omitidas", "Cortes", "Reinicios")
        self.tree_dias = ttk.Treeview(
            self.frame_tabla_dias, columns=cols_dias, show="headings", height=4
        )

        headers = {
            "Fecha": "Fecha / Día",
            "Vueltas": "Vueltas Realizadas",
            "Omitidas": "Geocercas Saltadas",
            "Cortes": "Cortes de Ruta",
            "Reinicios": "Reinicios",
        }

        for c in cols_dias:
            self.tree_dias.heading(c, text=headers[c])
            self.tree_dias.column(c, width=120, anchor="center")

        self.tree_dias.pack(fill="x", expand=True)

    def _crear_card_kpi(self, parent, titulo, val_def, col, color_val=None):
        card = tk.Frame(parent, bg=PaletaColores.CARD_OSCURA, padx=10, pady=6)
        card.grid(row=0, column=col, padx=3, pady=2, sticky="nsew")
        parent.columnconfigure(col, weight=1)

        lbl_t = tk.Label(
            card,
            text=titulo,
            bg=PaletaColores.CARD_OSCURA,
            fg=PaletaColores.TEXTO_MUTED,
            font=("Segoe UI", 7, "bold"),
        )
        lbl_t.pack(anchor="w")

        lbl_v = tk.Label(
            card,
            text=val_def,
            bg=PaletaColores.CARD_OSCURA,
            fg=color_val if color_val else PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 10, "bold"),
        )
        lbl_v.pack(anchor="w", pady=(2, 0))
        return lbl_t, lbl_v

    def cargar_datos(self, df_resultado: pd.DataFrame, es_semanal: bool = False):
        self.df_resultado = df_resultado
        self.es_semanal = es_semanal

        if self.es_semanal:
            self.lbl_modo_reporte.config(text="MODO: ANÁLISIS SEMANAL", fg=PaletaColores.AMARILLO_ADVERTENCIA)
            self.frame_tabla_dias.pack(fill="x", pady=(5, 0))
        else:
            self.lbl_modo_reporte.config(text="MODO: TRAYECTORIA DIARIA", fg=PaletaColores.VERDE_EXITO)
            self.frame_tabla_dias.pack_forget()

        if df_resultado is None or df_resultado.empty:
            return

        unidades = df_resultado["Agrupación"].unique().tolist()
        self.cb_unidades["values"] = unidades
        if unidades:
            self.cb_unidades.current(0)
            self._al_seleccionar_unidad(None)

    def _al_seleccionar_unidad(self, event):
        unidad_sel = self.cb_unidades.get()
        if not unidad_sel or self.df_resultado is None or self.df_resultado.empty:
            return

        df_u = self.df_resultado[
            self.df_resultado["Agrupación"].astype(str).str.strip() == unidad_sel
        ]

        if df_u.empty:
            return

        if self.toolbar_diaria:
            self.toolbar_diaria.destroy()
            self.toolbar_diaria = None
        if self.canvas_diaria:
            self.canvas_diaria.get_tk_widget().destroy()
            self.canvas_diaria = None

        if self.es_semanal:
            self.card_title_1.config(text="VUELTAS SEMANALES")
            self.card_title_2.config(text="DÍAS TRABAJADOS")
            self.card_title_3.config(text="PROMEDIO VTS / DÍA")
            self.card_title_4.config(text="GEOCERCAS SALTADAS")
            self.card_title_5.config(text="CORTES / REINICIOS")
            self.card_title_6.config(text="MÁXIMO RETRASO")

            metricas = GraficaSemanalBuilder.calcular_metricas_semanales_reales(df_u)

            max_retraso_str = "0m (A Tiempo)"
            mask_retrasos = df_u["Desfase"].astype(str).str.contains(r"\+")
            if mask_retrasos.any():
                primer_retraso = df_u[mask_retrasos].iloc[0]
                max_retraso_str = f"{primer_retraso.get('Desfase', '')} ({str(primer_retraso.get('Geocerca', '')).replace(' (Faltante)', '')})"

            self.lbl_card_1.config(text=str(metricas["vueltas_totales"]))
            self.lbl_card_2.config(text=f"{metricas['dias_trabajados']} días")
            self.lbl_card_3.config(text=f"{metricas['promedio_diario']} vts/día")
            self.lbl_card_4.config(text=str(metricas["saltadas"]))
            self.lbl_card_5.config(text=f"{metricas['cortes']} Cort. / {metricas['reinicios']} Rein.")
            self.lbl_card_6.config(text=max_retraso_str)

            for item in self.tree_dias.get_children():
                self.tree_dias.delete(item)

            df_desg = metricas["df_desglose_dias"]
            if not df_desg.empty:
                for _, r_dia in df_desg.iterrows():
                    self.tree_dias.insert(
                        "",
                        "end",
                        values=(
                            r_dia["Fecha"],
                            r_dia["Vueltas"],
                            r_dia["Omitidas"],
                            r_dia["Cortes"],
                            r_dia["Reinicios"],
                        ),
                    )

            fig = GraficaSemanalBuilder.crear_dashboard_semanal_unidad(df_u, unidad_sel)

        else:
            self.card_title_1.config(text="HORA INICIO")
            self.card_title_2.config(text="HORA TERMINO")
            self.card_title_3.config(text="GEOCERCA INICIO")
            self.card_title_4.config(text="VUELTAS TOTALES")
            self.card_title_5.config(text="REINICIOS / CORTES")
            self.card_title_6.config(text="MÁXIMO RETRASO")

            p_reg = df_u.iloc[0]
            u_reg = df_u.iloc[-1]

            self.lbl_card_1.config(text=str(p_reg.get("Entrada", "-")))
            self.lbl_card_2.config(text=str(u_reg.get("Salida", "-")))
            self.lbl_card_3.config(text=str(p_reg.get("Geocerca", "-")).replace(" (Faltante)", ""))

            vueltas = df_u["Vuelta_Num"].max() if "Vuelta_Num" in df_u.columns else 1
            self.lbl_card_4.config(text=str(int(vueltas)))

            reinicios = df_u["Estado_Ruta"].astype(str).str.contains("Reinicio").sum()
            cortes = df_u["Estado_Ruta"].astype(str).str.contains("CORTE").sum()
            self.lbl_card_5.config(text=f"{reinicios} Rein. / {cortes} Cort.")

            max_retraso_str = "0m (A Tiempo)"
            mask_retrasos = df_u["Desfase"].astype(str).str.contains(r"\+")
            if mask_retrasos.any():
                primer_retraso = df_u[mask_retrasos].iloc[0]
                max_retraso_str = f"{primer_retraso.get('Desfase', '')} ({str(primer_retraso.get('Geocerca', '')).replace(' (Faltante)', '')})"
            self.lbl_card_6.config(text=max_retraso_str)

            fig = GraficaDiariaBuilder.crear_grafica_trayectoria(df_u)

        self.canvas_diaria = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self.canvas_diaria.draw()
        self.toolbar_diaria = NavigationToolbar2Tk(self.canvas_diaria, self.frame_grafico)
        self.toolbar_diaria.update()
        self.toolbar_diaria.pack(side="bottom", fill="x")
        self.canvas_diaria.get_tk_widget().pack(fill="both", expand=True)

    def _maximizar_grafica(self):
        """Abre la gráfica en una ventana emergente a pantalla completa con controles de zoom."""
        unidad_sel = self.cb_unidades.get()
        if not unidad_sel or self.df_resultado is None or self.df_resultado.empty:
            return

        df_u = self.df_resultado[
            self.df_resultado["Agrupación"].astype(str).str.strip() == unidad_sel
        ]

        top = tk.Toplevel(self)
        top.title(f"Gráfica Ampliada — Unidad {unidad_sel}")
        top.geometry("1400x850")
        top.configure(bg=PaletaColores.PANEL_LATERAL)

        if self.es_semanal:
            fig = GraficaSemanalBuilder.crear_dashboard_semanal_unidad(df_u, unidad_sel)
        else:
            fig = GraficaDiariaBuilder.crear_grafica_trayectoria(df_u)

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, top)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")
        canvas.get_tk_widget().pack(fill="both", expand=True)