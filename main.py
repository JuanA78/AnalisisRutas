import os
import sys
import warnings
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# ------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ------------------------------------------------------------
# IMPORTACIONES DE COMPONENTES Y SERVICIOS
# ------------------------------------------------------------
from configuracion.colores import PaletaColores
from configuracion.rutas_config import RutasConfig

from lectores_excel.lector_geocercas import LectorGeocercas
from lectores_excel.lector_actividad_gps import LectorActividadGPS
from servicios.ruta_service import RutaService
from servicios.servicio_resumen_general import ServicioResumenGeneral

# Importación de las 4 Páginas Principales
from interfaz.vista_resumen_general import VistaResumenGeneral
from interfaz.vista_actividad_geocercas import VistaActividadGeocercas
from interfaz.vista_graficas_contenedor import VistaGraficasContenedor
from interfaz.vista_actividad_diaria_gps import VistaActividadDiariaGPS


class VentanaPrincipal(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Analizador de Rutas 3000")
        self.geometry("1350x780")
        self.minsize(1100, 680)

        self.COLOR_FONDO = getattr(PaletaColores, "BG_PRINCIPAL", "#0F172A")
        self.COLOR_PANEL = getattr(PaletaColores, "PANEL_LATERAL", "#1E293B")
        self.COLOR_TEXTO = getattr(PaletaColores, "TEXTO_BLANCO", "#F8FAFC")

        self.configure(bg=self.COLOR_FONDO)

        # Estado de datos
        self.lector_geocercas = None
        self.lector_actividad = None

        self.df_geocercas_original = pd.DataFrame()
        self.df_actividad_gps = pd.DataFrame()

        self.df_unidades_seleccionadas = pd.DataFrame()
        self.df_resultado_actual = pd.DataFrame()
        self.df_resumen_actual = pd.DataFrame()

        # Tiempos de referencia por ruta
        self.tiempos_arbolito = {
            ("La Cruz", "Centro"): 17, ("Centro", "Polo Norte"): 8,
            ("Polo Norte", "Iberia"): 5, ("Iberia", "CTM"): 13,
            ("CTM", "Gavilan"): 10, ("Gavilan", "CTM"): 10,
            ("CTM", "Iberia"): 3, ("Iberia", "Polo Norte"): 5,
            ("Polo Norte", "Centro"): 12, ("Centro", "La Cruz"): 19,
        }

        self.tiempos_agua_salada = {
            ("Canal_CasaEloy", "Centro"): 9, ("Centro", "Polo Norte"): 6,
            ("Polo Norte", "Iberia"): 5, ("Iberia", "AguaSalada"): 11,
            ("AguaSalada", "Iberia"): 5, ("Iberia", "Polo Norte"): 5,
            ("Polo Norte", "Centro"): 10, ("Centro", "Canal_CasaEloy"): 12,
        }

        self._crear_interfaz()

    def _crear_interfaz(self):
        contenedor = tk.Frame(self, bg=self.COLOR_FONDO)
        contenedor.pack(fill="both", expand=True)

        self.panel_lateral = tk.Frame(contenedor, bg=self.COLOR_PANEL, width=320)
        self.panel_lateral.pack(side="left", fill="y", padx=(10, 5), pady=10)
        self.panel_lateral.pack_propagate(False)

        self.panel_principal = tk.Frame(contenedor, bg=self.COLOR_FONDO)
        self.panel_principal.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        self._crear_panel_lateral()
        self._crear_pestanas()

    def _crear_panel_lateral(self):
        tk.Label(
            self.panel_lateral, text="Analizador de Rutas 3000",
            font=("Segoe UI", 16, "bold"), bg=self.COLOR_PANEL, fg=self.COLOR_TEXTO
        ).pack(anchor="w", padx=15, pady=(18, 5))

        tk.Label(
            self.panel_lateral, text="Carga los reportes y selecciona las unidades.",
            font=("Segoe UI", 9), bg=self.COLOR_PANEL, fg="#CBD5E1"
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # Botones de Carga
        self._crear_boton(self.panel_lateral, "Subir archivo de geocercas", self.cargar_archivo_geocercas).pack(fill="x", padx=15, pady=5)
        self.lbl_geocercas = tk.Label(self.panel_lateral, text="Archivo de geocercas pendiente", bg=self.COLOR_PANEL, fg="#CBD5E1", font=("Segoe UI", 9))
        self.lbl_geocercas.pack(anchor="w", padx=15, pady=(0, 10))

        self._crear_boton(self.panel_lateral, "Subir archivo de actividad GPS", self.cargar_archivo_actividad).pack(fill="x", padx=15, pady=5)
        self.lbl_actividad = tk.Label(self.panel_lateral, text="Archivo de actividad GPS pendiente", bg=self.COLOR_PANEL, fg="#CBD5E1", font=("Segoe UI", 9))
        self.lbl_actividad.pack(anchor="w", padx=15, pady=(0, 15))

        # Selección de Ruta
        tk.Label(self.panel_lateral, text="Ruta de referencia", bg=self.COLOR_PANEL, fg=self.COLOR_TEXTO, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(5, 5))
        self.combo_ruta = ttk.Combobox(self.panel_lateral, values=["El Arbolito", "Agua Salada"], state="readonly")
        self.combo_ruta.pack(fill="x", padx=15, pady=(0, 12))
        self.combo_ruta.set("El Arbolito")
        self.combo_ruta.bind("<<ComboboxSelected>>", self._preseleccionar_unidades_por_ruta)

        # Unidades Listbox
        tk.Label(self.panel_lateral, text="Unidades disponibles", bg=self.COLOR_PANEL, fg=self.COLOR_TEXTO, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(0, 5))
        contenedor_unidades = tk.Frame(self.panel_lateral, bg=self.COLOR_PANEL)
        contenedor_unidades.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.lista_unidades = tk.Listbox(
            contenedor_unidades, selectmode=tk.EXTENDED, exportselection=False,
            bg="#0F172A", fg="#F8FAFC", selectbackground="#0284C7", selectforeground="#FFFFFF",
            relief="flat", font=("Segoe UI", 9)
        )
        self.lista_unidades.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(contenedor_unidades, orient="vertical", command=self.lista_unidades.yview)
        scrollbar.pack(side="right", fill="y")
        self.lista_unidades.configure(yscrollcommand=scrollbar.set)

        # Acciones Unidades
        btn_frame = tk.Frame(self.panel_lateral, bg=self.COLOR_PANEL)
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))
        tk.Button(btn_frame, text="Seleccionar todas", command=self.seleccionar_todas_unidades, bg="#334155", fg="white", relief="flat").pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(btn_frame, text="Limpiar selección", command=self.limpiar_seleccion_unidades, bg="#334155", fg="white", relief="flat").pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Analizar y Exportar
        self._crear_boton(self.panel_lateral, "Analizar rutas", self.ejecutar_analisis).pack(fill="x", padx=15, pady=(5, 10))
        tk.Button(self.panel_lateral, text="Exportar resumen a Excel", command=self.exportar_resumen, bg="#334155", fg="white", relief="flat").pack(fill="x", padx=15, pady=2)
        tk.Button(self.panel_lateral, text="Exportar detalle a Excel", command=self.exportar_detalle, bg="#334155", fg="white", relief="flat").pack(fill="x", padx=15, pady=(2, 10))

    def _crear_boton(self, parent, texto, comando):
        return tk.Button(parent, text=texto, command=comando, bg="#38BDF8", fg="#FFFFFF", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", pady=8)

    def _crear_pestanas(self):
        self.notebook = ttk.Notebook(self.panel_principal)
        self.notebook.pack(fill="both", expand=True)

        # Pestaña 1: Resumen General
        self.tab_resumen = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_resumen, text="Resumen general")
        self.vista_resumen = VistaResumenGeneral(self.tab_resumen)
        self.vista_resumen.pack(fill="both", expand=True)

        # Pestaña 2: Detalle de Rutas
        self.tab_detalle = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_detalle, text="Detalle de rutas")
        self.vista_detalle = VistaActividadGeocercas(self.tab_detalle)
        self.vista_detalle.pack(fill="both", expand=True)

        # Pestaña 3: Gráficas
        self.tab_graficas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_graficas, text="Gráficas")
        self.vista_graficas = VistaGraficasContenedor(self.tab_graficas)
        self.vista_graficas.pack(fill="both", expand=True)

        # Pestaña 4: Actividad Diaria GPS
        self.tab_gps = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gps, text="Actividad diaria GPS")
        self.vista_gps = VistaActividadDiariaGPS(self.tab_gps)
        self.vista_gps.pack(fill="both", expand=True)

    # ------------------------------------------------------------
    # EVENTOS DE ARCHIVOS Y SELECCIÓN
    # ------------------------------------------------------------
    def cargar_archivo_geocercas(self):
        archivo = filedialog.askopenfilename(title="Seleccionar geocercas", filetypes=[("Archivos Excel", "*.xlsx *.xls")])
        if not archivo:
            return
        try:
            lector = LectorGeocercas(archivo)
            df = lector.df_raw
            unidades = lector.obtener_unidades()

            if not unidades:
                messagebox.showwarning("Sin datos", "No se encontraron unidades.")
                return

            self.lector_geocercas = lector
            self.df_geocercas_original = df.copy()
            self.lista_unidades.delete(0, tk.END)
            for u in unidades:
                self.lista_unidades.insert(tk.END, str(u))

            self._preseleccionar_unidades_por_ruta()
            self.lbl_geocercas.config(text=f"Cargado: {os.path.basename(archivo)}", fg="#86EFAC")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cargar_archivo_actividad(self):
        archivo = filedialog.askopenfilename(title="Seleccionar actividad GPS", filetypes=[("Archivos Excel", "*.xlsx *.xls")])
        if not archivo:
            return
        try:
            lector = LectorActividadGPS(archivo)
            df = lector.cargar_datos()
            if df is None or df.empty:
                return

            self.lector_actividad = lector
            self.df_actividad_gps = df.copy()

            # Pestaña 4: Cargar todos los datos inicialmente
            self.vista_gps.cargar_datos(self.df_actividad_gps)
            self.lbl_actividad.config(text=f"Cargado: {os.path.basename(archivo)}", fg="#86EFAC")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def seleccionar_todas_unidades(self):
        self.lista_unidades.selection_set(0, tk.END)

    def limpiar_seleccion_unidades(self):
        self.lista_unidades.selection_clear(0, tk.END)

    def _preseleccionar_unidades_por_ruta(self, event=None):
        if self.lista_unidades.size() == 0:
            return
        ruta = self.combo_ruta.get()
        self.lista_unidades.selection_clear(0, tk.END)
        for i in range(self.lista_unidades.size()):
            unidad = self.lista_unidades.get(i)
            try:
                if RutasConfig.obtener_ruta_predeterminada(unidad) == ruta:
                    self.lista_unidades.selection_set(i)
            except Exception:
                continue

    def _obtener_unidades_seleccionadas(self):
        return [self.lista_unidades.get(i) for i in self.lista_unidades.curselection()]

    def _obtener_tiempos_objetivo(self):
        return self.tiempos_agua_salada.copy() if self.combo_ruta.get() == "Agua Salada" else self.tiempos_arbolito.copy()

    # ------------------------------------------------------------
    # EJECUTAR ANÁLISIS
    # ------------------------------------------------------------
    def ejecutar_analisis(self):
        if self.lector_geocercas is None or self.df_geocercas_original.empty:
            messagebox.showwarning("Falta archivo", "Carga el archivo de geocercas.")
            return

        unidades_sel = self._obtener_unidades_seleccionadas()
        if not unidades_sel:
            messagebox.showwarning("Atención", "Selecciona al menos una unidad.")
            return

        try:
            # 1. Obtener datos de unidades seleccionadas y procesar
            df_unidades = self.lector_geocercas.obtener_datos_unidades(unidades_sel)
            df_resultado = RutaService.analizar_unidades(df_unidades, tiempos_objetivo=self._obtener_tiempos_objetivo())

            if df_resultado is None or df_resultado.empty:
                return

            self.df_resultado_actual = df_resultado.copy()
            df_resumen_diario = RutaService.obtener_resumen_diario_unidades(df_unidades)

            # 2. Consolidación profesional vía ServicioResumenGeneral
            df_resumen_general = ServicioResumenGeneral.preparar_resumen_general(
                df_resumen_diario=df_resumen_diario,
                df_resultado_geocercas=df_resultado,
                df_actividad_gps=self.df_actividad_gps
            )
            self.df_resumen_actual = df_resumen_general.copy()

            # 3. ACTUALIZAR LAS 4 VISTAS
            # Enviamos tanto el resumen consolidado como el detalle procesado a la vista de resumen
            self.vista_resumen.cargar_datos(df_resumen_general, df_resultado)
            self.vista_detalle.cargar_datos(df_resultado)
            self.vista_graficas.cargar_datos(df_resultado)
            self.vista_gps.cargar_datos(self.df_actividad_gps, unidades_sel)

            self.notebook.select(self.tab_resumen)
            messagebox.showinfo("Éxito", "Análisis completado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error en el análisis:\n{e}")

    def exportar_resumen(self):
        if self.df_resumen_actual.empty:
            return
        arch = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="resumen_rutas.xlsx")
        if arch:
            self.df_resumen_actual.to_excel(arch, index=False)

    def exportar_detalle(self):
        if self.df_resultado_actual.empty:
            return
        arch = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="detalle_rutas.xlsx")
        if arch:
            self.df_resultado_actual.to_excel(arch, index=False)


if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()