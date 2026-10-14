# interfaz/vista_tabla_individual.py
import tkinter as tk
from tkinter import ttk
import pandas as pd
from configuracion.colores import PaletaColores


class VistaTablaIndividual(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.df_resultado = None
        self.configure(style="Main.TFrame")
        self._crear_layout()

    def _crear_layout(self):
        frame_top = tk.Frame(self, bg=PaletaColores.PANEL_LATERAL, padx=12, pady=10)
        frame_top.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            frame_top,
            text="Seleccionar Unidad:",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.cb_unidades = ttk.Combobox(
            frame_top, state="readonly", width=22, font=("Segoe UI", 10)
        )
        self.cb_unidades.pack(side="left")
        self.cb_unidades.bind("<<ComboboxSelected>>", self._al_seleccionar_unidad)

        self.lbl_total_regs = tk.Label(
            frame_top,
            text="0 registros procesados",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.TEXTO_MUTED,
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_total_regs.pack(side="right")

        frame_tabla = tk.Frame(self, bg=PaletaColores.BG_PRINCIPAL)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        cols = (
            "Unidad",
            "Geocerca",
            "Entrada",
            "Salida",
            "Tiempo_Real",
            "Tiempo_Estimado",
            "Desfase",
            "Estado_Ruta",
        )

        self.tree = ttk.Treeview(
            frame_tabla, columns=cols, show="headings", height=18
        )

        headers = {
            "Unidad": "Unidad",
            "Geocerca": "Geocerca",
            "Entrada": "Entrada",
            "Salida": "Salida",
            "Tiempo_Real": "Tiempo Real",
            "Tiempo_Estimado": "Tiempo Estimado",
            "Desfase": "Desfase",
            "Estado_Ruta": "Estado Ruta",
        }

        widths = {
            "Unidad": 80,
            "Geocerca": 140,
            "Entrada": 150,
            "Salida": 160,
            "Tiempo_Real": 110,
            "Tiempo_Estimado": 120,
            "Desfase": 100,
            "Estado_Ruta": 130,
        }

        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="center")

        self.tree.tag_configure("tag_no_registrada", background="#FEF3C7", foreground="#92400E")
        self.tree.tag_configure("tag_retraso", background="#FEE2E2", foreground="#991B1B")
        self.tree.tag_configure("tag_atiempo", background="#DCFCE7", foreground="#166534")
        self.tree.tag_configure("tag_inicio", background="#FFFFFF", foreground="#0F172A")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def cargar_datos(self, df_resultado: pd.DataFrame):
        self.df_resultado = df_resultado
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

        for item in self.tree.get_children():
            self.tree.delete(item)

        df_u = self.df_resultado[
            self.df_resultado["Agrupación"].astype(str).str.strip() == unidad_sel
        ]

        self.lbl_total_regs.config(text=f"{len(df_u)} registros procesados")

        for _, r in df_u.iterrows():
            est = str(r.get("Estado_Ruta", ""))
            desfase = str(r.get("Desfase", ""))

            if "NO REGISTRADA" in est or "Omitida" in str(r.get("Tipo", "")):
                tag_style = "tag_no_registrada"
            elif "+" in desfase:
                tag_style = "tag_retraso"
            elif "-" in desfase and desfase != "-":
                tag_style = "tag_atiempo"
            else:
                tag_style = "tag_inicio"

            self.tree.insert(
                "",
                "end",
                values=(
                    r.get("Agrupación", "-"),
                    r.get("Geocerca", "-"),
                    r.get("Entrada", "-"),
                    r.get("Salida", "-"),
                    r.get("Tiempo_Real", "-"),
                    r.get("Tiempo_Estimado", "-"),
                    r.get("Desfase", "-"),
                    est,
                ),
                tags=(tag_style,),
            )