import tkinter as tk
from tkinter import ttk
import pandas as pd

from interfaz.vista_grafica_circular_estadisticos import VistaGraficaCircularEstadisticos
from interfaz.vista_grafica_trazo_recorrido import VistaGraficaTrazoRecorrido


class VistaGraficasContenedor(ttk.Frame):
    """Contenedor que agrupa las vistas de visualización gráfica."""

    def __init__(self, parent):
        super().__init__(parent)
        self._crear_interfaz()

    def _crear_interfaz(self):
        self.notebook_graficas = ttk.Notebook(self)
        self.notebook_graficas.pack(fill="both", expand=True)

        # Sub-pestaña 1: Estadísticos (Pie Chart)
        self.tab_pie = ttk.Frame(self.notebook_graficas)
        self.notebook_graficas.add(self.tab_pie, text="Estadísticos")
        self.vista_pie = VistaGraficaCircularEstadisticos(self.tab_pie)
        self.vista_pie.pack(fill="both", expand=True)

        # Sub-pestaña 2: Trazo del recorrido
        self.tab_trazo = ttk.Frame(self.notebook_graficas)
        self.notebook_graficas.add(self.tab_trazo, text="Trazo del recorrido")
        self.vista_trazo = VistaGraficaTrazoRecorrido(self.tab_trazo)
        self.vista_trazo.pack(fill="both", expand=True)

    def cargar_datos(self, df_resultado: pd.DataFrame):
        """Transfiere los datos analizados a cada subgráfica."""
        self.vista_pie.cargar_datos(df_resultado)
        self.vista_trazo.cargar_datos(df_resultado)