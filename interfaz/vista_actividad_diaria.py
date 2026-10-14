# interfaz/vista_actividad_diaria.py
import tkinter as tk
from tkinter import ttk
import pandas as pd
from configuracion.colores import PaletaColores


class VistaActividadDiaria(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.configure(style="Main.TFrame")
        self._crear_layout()

    def _crear_layout(self):
        frame_top = tk.Frame(self, bg=PaletaColores.PANEL_LATERAL, padx=12, pady=8)
        frame_top.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            frame_top,
            text="📑 REGISTROS DE ACTIVIDAD DIARIA DE LA FLOTA",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")

        self.lbl_conteo = tk.Label(
            frame_top,
            text="0 Registros",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_conteo.pack(side="right")

        frame_tabla = tk.Frame(self, bg=PaletaColores.BG_PRINCIPAL)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.tabla = ttk.Treeview(frame_tabla, show="headings", height=15)
        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tabla.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tabla.xview)
        self.tabla.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tabla.pack(fill="both", expand=True)

    def cargar_datos(self, df_actividad: pd.DataFrame):
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        if df_actividad is None or df_actividad.empty:
            self.lbl_conteo.config(text="0 Registros")
            return

        columnas = list(df_actividad.columns)
        self.tabla["columns"] = columnas

        for col in columnas:
            self.tabla.heading(col, text=str(col))
            self.tabla.column(col, width=120, anchor="center")

        for _, row in df_actividad.iterrows():
            vals = [str(v) if pd.notna(v) else "-" for v in row.values]
            self.tabla.insert("", "end", values=vals)

        self.lbl_conteo.config(text=f"{len(df_actividad)} Registros Cargados")