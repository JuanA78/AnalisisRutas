import tkinter as tk
from tkinter import ttk
import pandas as pd

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)

from configuracion.colores import PaletaColores
from visualizaciones.grafica_trazo_recorrido import GraficaTrazoRecorrido


class VistaGraficaTrazoRecorrido(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.df_resultado = pd.DataFrame()
        self.canvas_diaria = None
        self.toolbar_diaria = None

        self.configure(style="Main.TFrame")
        self._crear_layout()

    def _crear_layout(self):
        frame_top = tk.Frame(
            self,
            bg=PaletaColores.PANEL_LATERAL,
            padx=12,
            pady=8,
        )
        frame_top.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            frame_top,
            text="Seleccionar Unidad para Recorrido:",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.cb_unidades = ttk.Combobox(
            frame_top,
            state="readonly",
            width=22,
            font=("Segoe UI", 10),
        )
        self.cb_unidades.pack(side="left")
        self.cb_unidades.bind(
            "<<ComboboxSelected>>",
            self._al_seleccionar_unidad,
        )

        tk.Button(
            frame_top,
            text="🔍 Maximizar Gráfica",
            bg=PaletaColores.AZUL_OCEANO,
            fg="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=10,
            command=self._maximizar_grafica,
        ).pack(side="right", padx=(10, 0))

        self.frame_cards = tk.Frame(
            self,
            bg=PaletaColores.PANEL_LATERAL,
            padx=10,
            pady=8,
        )
        self.frame_cards.pack(fill="x", padx=10, pady=(0, 5))

        self.card_title_1, self.lbl_card_1 = self._crear_card_kpi(
            self.frame_cards, "HORA INICIO", "-", 0
        )
        self.card_title_2, self.lbl_card_2 = self._crear_card_kpi(
            self.frame_cards, "HORA TÉRMINO", "-", 1
        )
        self.card_title_3, self.lbl_card_3 = self._crear_card_kpi(
            self.frame_cards, "GEOCERCA INICIO", "-",
            2, PaletaColores.CELESTE_VIBRANTE
        )
        self.card_title_4, self.lbl_card_4 = self._crear_card_kpi(
            self.frame_cards, "VUELTAS TOTALES", "0",
            3, PaletaColores.VERDE_EXITO
        )
        self.card_title_5, self.lbl_card_5 = self._crear_card_kpi(
            self.frame_cards, "REINICIOS / CORTES", "0",
            4, "#8B5CF6"
        )
        self.card_title_6, self.lbl_card_6 = self._crear_card_kpi(
            self.frame_cards, "MÁXIMO RETRASO", "-",
            5, PaletaColores.ROJO_ALERTA
        )

        self.frame_grafico = tk.Frame(
            self,
            bg=PaletaColores.BG_PRINCIPAL,
        )
        self.frame_grafico.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(5, 10),
        )

    def _crear_card_kpi(
        self, parent, titulo, valor, columna, color_val=None
    ):
        card = tk.Frame(
            parent,
            bg=PaletaColores.CARD_OSCURA,
            padx=10,
            pady=6,
        )
        card.grid(
            row=0,
            column=columna,
            padx=3,
            pady=2,
            sticky="nsew",
        )
        parent.columnconfigure(columna, weight=1)

        titulo_label = tk.Label(
            card,
            text=titulo,
            bg=PaletaColores.CARD_OSCURA,
            fg=PaletaColores.TEXTO_MUTED,
            font=("Segoe UI", 7, "bold"),
        )
        titulo_label.pack(anchor="w")

        valor_label = tk.Label(
            card,
            text=valor,
            bg=PaletaColores.CARD_OSCURA,
            fg=color_val or PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 10, "bold"),
        )
        valor_label.pack(anchor="w", pady=(2, 0))

        return titulo_label, valor_label

    def cargar_datos(self, df_resultado: pd.DataFrame):
        self.df_resultado = (
            df_resultado.copy()
            if df_resultado is not None
            else pd.DataFrame()
        )

        if self.df_resultado.empty:
            self.cb_unidades["values"] = []
            self.cb_unidades.set("")
            self._limpiar_grafica()
            return

        col_agrupa = next((c for c in self.df_resultado.columns if "AGRUPA" in c.upper() or "UNIDAD" in c.upper()), None)
        if not col_agrupa:
            return

        unidades = sorted(
            self.df_resultado[col_agrupa]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        self.cb_unidades["values"] = unidades

        if unidades:
            self.cb_unidades.current(0)
            self._al_seleccionar_unidad()

    def _limpiar_grafica(self):
        if self.toolbar_diaria is not None:
            self.toolbar_diaria.destroy()
            self.toolbar_diaria = None

        if self.canvas_diaria is not None:
            self.canvas_diaria.get_tk_widget().destroy()
            self.canvas_diaria = None

    def _al_seleccionar_unidad(self, event=None):
        unidad = self.cb_unidades.get()

        if not unidad or self.df_resultado.empty:
            return

        col_agrupa = next((c for c in self.df_resultado.columns if "AGRUPA" in c.upper() or "UNIDAD" in c.upper()), "Agrupación")

        df_u = self.df_resultado[
            self.df_resultado[col_agrupa].astype(str).str.strip() == unidad.strip()
        ].copy()

        if df_u.empty:
            return

        self._limpiar_grafica()

        primera = df_u.iloc[0]
        ultima = df_u.iloc[-1]

        self.lbl_card_1.config(text=str(primera.get("Entrada", primera.get("Salida", "-"))))
        self.lbl_card_2.config(text=str(ultima.get("Salida", ultima.get("Entrada", "-"))))
        self.lbl_card_3.config(
            text=str(primera.get("Geocerca", "-")).replace(" (Faltante)", "")
        )

        vueltas = (
            df_u["Vuelta_Num"].max()
            if "Vuelta_Num" in df_u.columns
            else 1
        )
        self.lbl_card_4.config(text=str(int(vueltas)))

        estados = (
            df_u["Estado_Ruta"].fillna("").astype(str)
            if "Estado_Ruta" in df_u.columns
            else pd.Series("", index=df_u.index)
        )

        reinicios = estados.str.contains("Reinicio", case=False).sum()
        cortes = estados.str.contains("CORTE", case=False).sum()

        self.lbl_card_5.config(text=f"{reinicios} Rein. / {cortes} Cort.")

        desfases = (
            df_u["Desfase"].fillna("").astype(str)
            if "Desfase" in df_u.columns
            else pd.Series("", index=df_u.index)
        )

        retrasos = df_u[desfases.str.startswith("+")]
        max_retraso = "0m (A Tiempo)"

        if not retrasos.empty:
            retraso_mayor = max(
                retrasos["Desfase"].astype(str),
                key=lambda x: self._segundos_desfase(x),
            )
            fila = retrasos[
                retrasos["Desfase"].astype(str) == retraso_mayor
            ].iloc[0]

            max_retraso = (
                f"{retraso_mayor} "
                f"({str(fila.get('Geocerca', '-')).replace(' (Faltante)', '')})"
            )

        self.lbl_card_6.config(text=max_retraso)

        fig = GraficaTrazoRecorrido.crear_grafica_trayectoria(df_u)

        self.canvas_diaria = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        self.canvas_diaria.draw()

        self.toolbar_diaria = NavigationToolbar2Tk(self.canvas_diaria, self.frame_grafico)
        self.toolbar_diaria.update()
        self.toolbar_diaria.pack(side="bottom", fill="x")

        self.canvas_diaria.get_tk_widget().pack(fill="both", expand=True)

    @staticmethod
    def _segundos_desfase(valor):
        import re
        coincidencia = re.search(r"(\d+)\s*m\s*(\d+)\s*s", str(valor))
        if coincidencia:
            return int(coincidencia.group(1)) * 60 + int(coincidencia.group(2))
        return 0

    def _maximizar_grafica(self):
        unidad = self.cb_unidades.get()
        if not unidad or self.df_resultado.empty:
            return

        col_agrupa = next((c for c in self.df_resultado.columns if "AGRUPA" in c.upper() or "UNIDAD" in c.upper()), "Agrupación")

        df_u = self.df_resultado[
            self.df_resultado[col_agrupa].astype(str).str.strip() == unidad.strip()
        ].copy()

        if df_u.empty:
            return

        top = tk.Toplevel(self)
        top.title(f"Gráfica Ampliada — Unidad {unidad}")
        top.geometry("1400x850")
        top.configure(bg=PaletaColores.PANEL_LATERAL)

        fig = GraficaTrazoRecorrido.crear_grafica_trayectoria(df_u)

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, top)
        toolbar.update()
        toolbar.pack(side="bottom", fill="x")

        canvas.get_tk_widget().pack(fill="both", expand=True)