import tkinter as tk
from tkinter import ttk
import pandas as pd

from configuracion.colores import PaletaColores
from servicios.servicio_actividad_gps import ServicioActividadGPS


class VistaActividadDiariaGPS(ttk.Frame):
    """Componente visual para desplegar la tabla de Actividad GPS."""

    COLOR_ENCABEZADO_BG = "#0F172A"  # Fondo personalizado para encabezados

    def __init__(self, parent):
        super().__init__(parent)
        self._crear_interfaz()

    def _crear_interfaz(self):
        contenedor = ttk.Frame(self)
        contenedor.pack(fill="both", expand=True, padx=10, pady=10)

        # ----------------------------------------------------
        # CONFIGURACIÓN DE ESTILOS
        # ----------------------------------------------------
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

        # Estilo del encabezado con fondo #0F172A
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

        # Barras de desplazamiento
        scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=self.tabla_gps.yview)
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tabla_gps.xview)
        scroll_x.pack(side="bottom", fill="x")

        self.tabla_gps.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    def cargar_datos(self, df_actividad: pd.DataFrame, unidades_sel: list = None):
        """Filtra los datos con el servicio y renderiza las filas en la tabla."""
        self.tabla_gps.delete(*self.tabla_gps.get_children())

        # Filtrar mediante la capa de servicio
        df = ServicioActividadGPS.filtrar_actividad(df_actividad, unidades_sel)

        if df is None or df.empty:
            self.tabla_gps["columns"] = ()
            return

        columnas = [str(col) for col in df.columns]
        self.tabla_gps["columns"] = columnas

        for columna in columnas:
            self.tabla_gps.heading(columna, text=columna)
            self.tabla_gps.column(columna, width=140, minwidth=80, anchor="w")

        for i, (_, fila) in enumerate(df.iterrows()):
            valores = [
                "" if pd.isna(valor) else str(valor)
                for valor in fila.tolist()
            ]
            tag_fila = "fila_par" if i % 2 == 0 else "fila_impar"
            self.tabla_gps.insert("", "end", values=valores, tags=(tag_fila,))

    @staticmethod
    def obtener_resumen_actividad(df_actividad: pd.DataFrame, unidades_sel: list = None) -> pd.DataFrame:
        return ServicioActividadGPS.filtrar_actividad(df_actividad, unidades_sel)

    @staticmethod
    def obtener_unidades(df_actividad: pd.DataFrame) -> list:
        return ServicioActividadGPS.obtener_unidades(df_actividad)