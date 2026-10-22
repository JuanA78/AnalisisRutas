import tkinter as tk
from tkinter import ttk
import pandas as pd

from configuracion.colores import PaletaColores
from lectores_excel.lector_actividad_gps import LectorActividadGPS


class VistaActividadDiariaGPS(ttk.Frame):
    """Componente visual para desplegar la tabla de Actividad GPS basada en LectorActividadGPS."""

    COLOR_ENCABEZADO_BG = "#0F172A"

    def __init__(self, parent):
        super().__init__(parent)
        self._crear_interfaz()

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self)
        contenedor.pack(fill="both", expand=True, padx=10, pady=10)

        estilo = ttk.Style()

        # Estilo de la tabla
        estilo.configure(
            "GPSTable.Treeview",
            background=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            foreground=getattr(PaletaColores, "TEXTO_BLANCO", "#FFFFFF"),
            fieldbackground=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            rowheight=28,
            font=("Segoe UI", 9)
        )

        estilo.map(
            "GPSTable.Treeview",
            background=[("selected", getattr(PaletaColores, "AZUL_OCEANO", "#0284C7"))],
            foreground=[("selected", getattr(PaletaColores, "TEXTO_BLANCO", "#FFFFFF"))]
        )

        # Estilo del encabezado
        estilo.configure(
            "GPSTable.Treeview.Heading",
            background=self.COLOR_ENCABEZADO_BG,
            foreground=getattr(PaletaColores, "CELESTE_VIBRANTE", "#38BDF8"),
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        estilo.map(
            "GPSTable.Treeview.Heading",
            background=[("active", getattr(PaletaColores, "CARD_BG", "#2A364F"))],
            foreground=[("active", getattr(PaletaColores, "TEXTO_BLANCO", "#FFFFFF"))]
        )

        # Crear Treeview
        self.tabla_gps = ttk.Treeview(
            contenedor,
            show="headings",
            style="GPSTable.Treeview"
        )
        self.tabla_gps.pack(side="left", fill="both", expand=True)

        # Tags para filas alternadas
        self.tabla_gps.tag_configure(
            "fila_par",
            background=getattr(PaletaColores, "CARD_OSCURA", "#0F172A")
        )
        self.tabla_gps.tag_configure(
            "fila_impar",
            background=getattr(PaletaColores, "CARD_BG", "#2A364F")
        )

        # Scrollbars
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_gps.yview)
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tabla_gps.xview)
        scroll_x.pack(side="bottom", fill="x")

        self.tabla_gps.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    def cargar_datos_desde_lector(self, filepath: str, ruta_seleccionada: str = None):
        """Carga y procesa el archivo Excel directamente desde LectorActividadGPS."""
        lector = LectorActividadGPS(filepath)
        df_datosgps = lector.cargar_datos_completos(ruta_seleccionada)
        self.cargar_datos(df_datosgps)

    def cargar_datos(self, df_actividad: pd.DataFrame):
        """Limpia el Treeview y renderiza las filas del DataFrame actualizado."""
        # Vaciado completo previo
        for i in self.tabla_gps.get_children():
            self.tabla_gps.delete(i)

        if df_actividad is None or df_actividad.empty:
            self.tabla_gps["columns"] = ()
            return

        columnas = [str(col) for col in df_actividad.columns]
        self.tabla_gps["columns"] = columnas

        for idx, col in enumerate(columnas):
            self.tabla_gps.heading(col, text=col)
            if idx == 0:
                anchura, alineacion = 140, "center"
            elif idx in [1, 2]:
                anchura, alineacion = 170, "center"
            elif idx in [3, 4]:
                anchura, alineacion = 140, "center"
            elif idx in [5, 6, 7]:
                anchura, alineacion = 150, "center"
            else:
                anchura, alineacion = 140, "w"

            self.tabla_gps.column(col, width=anchura, minwidth=90, anchor=alineacion)

        # Cargar las nuevas filas filtradas
        for i, (_, fila) in enumerate(df_actividad.iterrows()):
            valores = [
                "" if pd.isna(valor) else str(valor).strip()
                for valor in fila.tolist()
            ]
            tag_fila = "fila_par" if i % 2 == 0 else "fila_impar"
            self.tabla_gps.insert("", "end", values=valores, tags=(tag_fila,))

    @staticmethod
    def obtener_unidades_desde_df(df_actividad: pd.DataFrame) -> list:
        """Extrae la lista única de unidades leídas de la primera columna."""
        if df_actividad is None or df_actividad.empty:
            return []
        col_unid = df_actividad.columns[0]
        return sorted(df_actividad[col_unid].dropna().astype(str).str.strip().unique().tolist())