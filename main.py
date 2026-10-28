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

from interfaz.vista_resumen_general import VistaResumenGeneral
from interfaz.vista_actividad_geocercas import VistaActividadGeocercas
from interfaz.vista_graficas_contenedor import VistaGraficasContenedor
from interfaz.vista_actividad_diaria_gps import VistaActividadDiariaGPS


class VentanaPrincipal(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Analizador de Rutas 3000")
        self.geometry("1400x820")
        self.minsize(1150, 700)

        self.COLOR_FONDO = getattr(
            PaletaColores, "BG_PRINCIPAL", "#0F172A"
        )
        self.COLOR_PANEL = getattr(
            PaletaColores, "PANEL_LATERAL", "#1E293B"
        )
        self.COLOR_TEXTO = getattr(
            PaletaColores, "TEXTO_BLANCO", "#F8FAFC"
        )

        self.configure(bg=self.COLOR_FONDO)

        # ----------------------------------------------------
        # ESTADO DE LOS DATOS
        # ----------------------------------------------------
        self.lector_geocercas = None
        self.lector_actividad = None

        self.df_geocercas_original = pd.DataFrame()
        self.df_actividad_gps = pd.DataFrame()

        self.df_resultado_actual = pd.DataFrame()
        self.df_resumen_actual = pd.DataFrame()

        # ----------------------------------------------------
        # TIEMPOS META: EL ARBOLITO
        # ----------------------------------------------------
        self.tiempos_arbolito_ida = [
            (("La Cruz", "Centro"), tk.IntVar(value=17)),
            (("Centro", "Polo Norte"), tk.IntVar(value=8)),
            (("Polo Norte", "Iberia"), tk.IntVar(value=5)),
            (("Iberia", "CTM"), tk.IntVar(value=13)),
            (("CTM", "Gavilan"), tk.IntVar(value=3)),
        ]

        self.tiempos_arbolito_regreso = [
            (("Gavilan", "CTM"), tk.IntVar(value=3)),
            (("CTM", "Iberia"), tk.IntVar(value=3)),
            (("Iberia", "Polo Norte"), tk.IntVar(value=5)),
            (("Polo Norte", "Centro"), tk.IntVar(value=12)),
            (("Centro", "La Cruz"), tk.IntVar(value=19)),
        ]

        # ----------------------------------------------------
        # TIEMPOS META: AGUA SALADA
        # ----------------------------------------------------
        self.tiempos_agua_salada_ida = [
            (("Canal_CasaEloy", "Centro"), tk.IntVar(value=15)),
            (("Centro", "Polo Norte"), tk.IntVar(value=10)),
            (("Polo Norte", "Iberia"), tk.IntVar(value=8)),
            (("Iberia", "AguaSalada"), tk.IntVar(value=17)),
        ]

        self.tiempos_agua_salada_regreso = [
            (("AguaSalada", "Iberia"), tk.IntVar(value=17)),
            (("Iberia", "Polo Norte"), tk.IntVar(value=8)),
            (("Polo Norte", "Centro"), tk.IntVar(value=10)),
            (("Centro", "Canal_CasaEloy"), tk.IntVar(value=15)),
        ]

        self._crear_interfaz()

    # ========================================================
    # INTERFAZ PRINCIPAL
    # ========================================================
    def _crear_interfaz(self):
        contenedor = tk.Frame(self, bg=self.COLOR_FONDO)
        contenedor.pack(fill="both", expand=True)

        self.panel_lateral = tk.Frame(
            contenedor,
            bg=self.COLOR_PANEL,
            width=270
        )
        self.panel_lateral.pack(
            side="left",
            fill="y",
            padx=(8, 4),
            pady=8
        )
        self.panel_lateral.pack_propagate(False)

        self.panel_principal = tk.Frame(
            contenedor,
            bg=self.COLOR_FONDO
        )
        self.panel_principal.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(4, 8),
            pady=8
        )

        self._crear_panel_lateral()
        self._crear_pestanas()

    # ========================================================
    # PANEL LATERAL
    # ========================================================
    def _crear_panel_lateral(self):
        tk.Label(
            self.panel_lateral,
            text="Analizador de Rutas",
            font=("Segoe UI", 13, "bold"),
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXTO
        ).pack(anchor="w", padx=10, pady=(6, 4))

        self._crear_boton(
            self.panel_lateral,
            "📂 Cargar Geocercas",
            self.cargar_archivo_geocercas
        ).pack(fill="x", padx=10, pady=2)

        self._crear_boton(
            self.panel_lateral,
            "🛰️ Cargar Actividad GPS",
            self.cargar_archivo_actividad
        ).pack(fill="x", padx=10, pady=2)

        tk.Label(
            self.panel_lateral,
            text="Ruta de referencia",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXTO,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=10, pady=(4, 2))

        self.combo_ruta = ttk.Combobox(
            self.panel_lateral,
            values=["El Arbolito", "Agua Salada"],
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.combo_ruta.pack(fill="x", padx=10, pady=(0, 4))
        self.combo_ruta.set("El Arbolito")
        self.combo_ruta.bind(
            "<<ComboboxSelected>>",
            self._al_cambiar_ruta
        )

        # ----------------------------------------------------
        # TIEMPOS META EDITABLES
        # ----------------------------------------------------
        self.frame_tiempos_container = tk.LabelFrame(
            self.panel_lateral,
            text=" Tiempos Meta (min) ",
            bg=self.COLOR_PANEL,
            fg="#38BDF8",
            font=("Segoe UI", 8, "bold")
        )
        self.frame_tiempos_container.pack(
            fill="x",
            expand=False,
            padx=10,
            pady=(2, 4)
        )

        self.canvas_tiempos = tk.Canvas(
            self.frame_tiempos_container,
            bg=self.COLOR_PANEL,
            height=270,
            highlightthickness=0
        )

        self.scrollbar_tiempos = ttk.Scrollbar(
            self.frame_tiempos_container,
            orient="vertical",
            command=self.canvas_tiempos.yview
        )

        self.frame_tiempos_list = tk.Frame(
            self.canvas_tiempos,
            bg=self.COLOR_PANEL
        )

        self.frame_tiempos_list.bind(
            "<Configure>",
            lambda e: self.canvas_tiempos.configure(
                scrollregion=self.canvas_tiempos.bbox("all")
            )
        )

        self.canvas_tiempos.create_window(
            (0, 0),
            window=self.frame_tiempos_list,
            anchor="nw"
        )

        self.canvas_tiempos.configure(
            yscrollcommand=self.scrollbar_tiempos.set
        )

        self.canvas_tiempos.pack(
            side="left",
            fill="both",
            expand=True
        )
        self.scrollbar_tiempos.pack(side="right", fill="y")

        self._renderizar_tiempos_ruta()

        # ----------------------------------------------------
        # LISTA DE UNIDADES
        # MULTIPLE: CADA CLIC ALTERNA LA SELECCIÓN
        # ----------------------------------------------------
        tk.Label(
            self.panel_lateral,
            text="Unidades disponibles",
            bg=self.COLOR_PANEL,
            fg=self.COLOR_TEXTO,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=10, pady=(2, 1))

        contenedor_unidades = tk.Frame(
            self.panel_lateral,
            bg=self.COLOR_PANEL
        )
        contenedor_unidades.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 4)
        )

        self.lista_unidades = tk.Listbox(
            contenedor_unidades,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            bg="#0F172A",
            fg="#F8FAFC",
            selectbackground="#0284C7",
            selectforeground="#FFFFFF",
            relief="flat",
            font=("Segoe UI", 8)
        )
        self.lista_unidades.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar_unidades = ttk.Scrollbar(
            contenedor_unidades,
            orient="vertical",
            command=self.lista_unidades.yview
        )
        scrollbar_unidades.pack(side="right", fill="y")

        self.lista_unidades.configure(
            yscrollcommand=scrollbar_unidades.set
        )

        # ----------------------------------------------------
        # BOTONES DE SELECCIÓN
        # ----------------------------------------------------
        btn_frame = tk.Frame(
            self.panel_lateral,
            bg=self.COLOR_PANEL
        )
        btn_frame.pack(fill="x", padx=10, pady=(0, 4))

        tk.Button(
            btn_frame,
            text="Todas",
            command=self.seleccionar_todas_unidades,
            bg="#334155",
            fg="white",
            font=("Segoe UI", 8),
            relief="flat"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 1)
        )

        tk.Button(
            btn_frame,
            text="Limpiar",
            command=self.limpiar_seleccion_unidades,
            bg="#334155",
            fg="white",
            font=("Segoe UI", 8),
            relief="flat"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(1, 0)
        )

        # ----------------------------------------------------
        # ACCIONES PRINCIPALES
        # ----------------------------------------------------
        self._crear_boton(
            self.panel_lateral,
            "▶ Analizar Rutas",
            self.ejecutar_analisis
        ).pack(fill="x", padx=10, pady=(2, 4))

        tk.Button(
            self.panel_lateral,
            text="📊 Exportar Resumen Excel",
            command=self.exportar_resumen,
            bg="#1E293B",
            fg="#38BDF8",
            font=("Segoe UI", 8, "bold"),
            relief="solid",
            bd=1
        ).pack(fill="x", padx=10, pady=2)

        tk.Button(
            self.panel_lateral,
            text="📋 Exportar Detalle Excel",
            command=self.exportar_detalle,
            bg="#1E293B",
            fg="#38BDF8",
            font=("Segoe UI", 8, "bold"),
            relief="solid",
            bd=1
        ).pack(fill="x", padx=10, pady=(2, 6))

    def _crear_boton(self, parent, texto, comando):
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            bg="#0284C7",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            pady=4
        )

    # ========================================================
    # RENDERIZADO DE TIEMPOS META
    # ========================================================
    def _renderizar_tiempos_ruta(self):
        for child in self.frame_tiempos_list.winfo_children():
            child.destroy()

        ruta = self.combo_ruta.get()

        if ruta == "Agua Salada":
            lista_ida = self.tiempos_agua_salada_ida
            lista_regreso = self.tiempos_agua_salada_regreso
        else:
            lista_ida = self.tiempos_arbolito_ida
            lista_regreso = self.tiempos_arbolito_regreso

        tk.Label(
            self.frame_tiempos_list,
            text="--- TRAYECTO IDA ---",
            bg=self.COLOR_PANEL,
            fg="#38BDF8",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(2, 1), padx=2)

        for (origen, destino), var in lista_ida:
            row_f = tk.Frame(
                self.frame_tiempos_list,
                bg=self.COLOR_PANEL
            )
            row_f.pack(fill="x", pady=0, padx=2)

            tk.Label(
                row_f,
                text=f"{origen} ➔ {destino}",
                bg=self.COLOR_PANEL,
                fg="#F8FAFC",
                font=("Segoe UI", 8, "bold"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            tk.Spinbox(
                row_f,
                from_=1,
                to=120,
                textvariable=var,
                width=3,
                font=("Segoe UI", 8, "bold"),
                bg="#0F172A",
                fg="#FFFFFF",
                buttonbackground="#1E293B",
                relief="flat"
            ).pack(side="right")

        tk.Label(
            self.frame_tiempos_list,
            text="--- TRAYECTO REGRESO ---",
            bg=self.COLOR_PANEL,
            fg="#38BDF8",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(5, 1), padx=2)

        for (origen, destino), var in lista_regreso:
            row_f = tk.Frame(
                self.frame_tiempos_list,
                bg=self.COLOR_PANEL
            )
            row_f.pack(fill="x", pady=0, padx=2)

            tk.Label(
                row_f,
                text=f"{origen} ➔ {destino}",
                bg=self.COLOR_PANEL,
                fg="#F8FAFC",
                font=("Segoe UI", 8, "bold"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            tk.Spinbox(
                row_f,
                from_=1,
                to=120,
                textvariable=var,
                width=3,
                font=("Segoe UI", 8, "bold"),
                bg="#0F172A",
                fg="#FFFFFF",
                buttonbackground="#1E293B",
                relief="flat"
            ).pack(side="right")

    # ========================================================
    # PESTAÑAS
    # ========================================================
    def _crear_pestanas(self):
        self.notebook = ttk.Notebook(self.panel_principal)
        self.notebook.pack(fill="both", expand=True)

        self.tab_gps = ttk.Frame(self.notebook)
        self.notebook.add(
            self.tab_gps,
            text="Actividad diaria GPS"
        )
        self.vista_gps = VistaActividadDiariaGPS(self.tab_gps)
        self.vista_gps.pack(fill="both", expand=True)

        self.tab_resumen = ttk.Frame(self.notebook)
        self.notebook.add(
            self.tab_resumen,
            text="Resumen general"
        )
        self.vista_resumen = VistaResumenGeneral(self.tab_resumen)
        self.vista_resumen.pack(fill="both", expand=True)

        self.tab_graficas = ttk.Frame(self.notebook)
        self.notebook.add(
            self.tab_graficas,
            text="Gráficas"
        )
        self.vista_graficas = VistaGraficasContenedor(self.tab_graficas)
        self.vista_graficas.pack(fill="both", expand=True)

        self.tab_detalle = ttk.Frame(self.notebook)
        self.notebook.add(
            self.tab_detalle,
            text="Detalle de rutas"
                )
        self.vista_detalle = VistaActividadGeocercas(self.tab_detalle)
        self.vista_detalle.pack(fill="both", expand=True)
    # ========================================================
    # CARGAR GEOCERCAS
    # ========================================================
    def cargar_archivo_geocercas(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar geocercas",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )

        if not archivo:
            return

        try:
            lector = LectorGeocercas(archivo)
            df = lector.df_raw
            unidades = lector.obtener_unidades()

            if not unidades:
                messagebox.showwarning(
                    "Sin datos",
                    "No se encontraron unidades."
                )
                return

            self.lector_geocercas = lector
            self.df_geocercas_original = df.copy()

            self.lista_unidades.delete(0, tk.END)

            for unidad in unidades:
                self.lista_unidades.insert(tk.END, str(unidad))

            # Seleccionar solo las unidades que correspondan
            # a la ruta elegida.
            self._preseleccionar_unidades_por_ruta()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ========================================================
    # CARGAR ACTIVIDAD GPS
    # ========================================================
    def cargar_archivo_actividad(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar actividad GPS",
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )

        if not archivo:
            return

        try:
            ruta_seleccionada = self.combo_ruta.get()

            lector = LectorActividadGPS(archivo)
            df = lector.cargar_datos_completos(ruta_seleccionada)

            if df is None or df.empty:
                messagebox.showwarning(
                    "Sin datos",
                    "No se encontraron registros para la ruta seleccionada."
                )
                return

            self.lector_actividad = lector
            self.df_actividad_gps = df.copy()

            self.vista_gps.cargar_datos(self.df_actividad_gps)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ========================================================
    # SELECCIÓN DE UNIDADES
    # ========================================================

    def seleccionar_todas_unidades(self):
        if self.lista_unidades.size() > 0:
            self.lista_unidades.selection_set(0, tk.END)

    def limpiar_seleccion_unidades(self):
        self.lista_unidades.selection_clear(0, tk.END)

    def _al_cambiar_ruta(self, event=None):
        self._renderizar_tiempos_ruta()
        self._preseleccionar_unidades_por_ruta()

        # Si ya hay actividad GPS cargada, actualizarla para la ruta.
        if self.lector_actividad is not None:
            try:
                ruta = self.combo_ruta.get()
                df = self.lector_actividad.cargar_datos_completos(ruta)

                if df is not None and not df.empty:
                    self.df_actividad_gps = df.copy()
                else:
                    self.df_actividad_gps = pd.DataFrame()

                self.vista_gps.cargar_datos(self.df_actividad_gps)

            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"No se pudo actualizar la actividad GPS:\\n{e}"
                )

    def _preseleccionar_unidades_por_ruta(self, event=None):
        if self.lista_unidades.size() == 0:
            return

        ruta = self.combo_ruta.get().strip().casefold()

        if ruta == "el arbolito":
            unidades_predeterminadas = set(
                RutasConfig.UNIDADES_EL_ARBOLITO
            )
        elif ruta == "agua salada":
            unidades_predeterminadas = set(
                RutasConfig.UNIDADES_AGUA_SALADA
            )
        else:
            unidades_predeterminadas = set()

        # Limpiar selección de la ruta anterior.
        self.lista_unidades.selection_clear(0, tk.END)

        # Seleccionar únicamente las unidades predeterminadas
        # de la ruta actual.
        for i in range(self.lista_unidades.size()):
            unidad = self.lista_unidades.get(i)

            if unidad in unidades_predeterminadas:
                self.lista_unidades.selection_set(i)

    def _obtener_unidades_seleccionadas(self):
        return [
            self.lista_unidades.get(i)
            for i in self.lista_unidades.curselection()
        ]

    # ========================================================
    # TIEMPOS OBJETIVO
    # ========================================================

    def _obtener_tiempos_objetivo(self):
        ruta = self.combo_ruta.get()

        if ruta == "Agua Salada":
            lista_completa = (
                self.tiempos_agua_salada_ida
                + self.tiempos_agua_salada_regreso
            )
        else:
            lista_completa = (
                self.tiempos_arbolito_ida
                + self.tiempos_arbolito_regreso
            )

        return {
            par: var.get()
            for par, var in lista_completa
        }

    # ========================================================
    # ANÁLISIS PRINCIPAL
    # ========================================================
    def ejecutar_analisis(self):
        if (
            self.lector_geocercas is None
            or self.df_geocercas_original.empty
        ):
            messagebox.showwarning(
                "Falta archivo",
                "Carga el archivo de geocercas."
            )
            return

        unidades_sel = self._obtener_unidades_seleccionadas()

        if not unidades_sel:
            messagebox.showwarning(
                "Atención",
                "Selecciona al menos una unidad."
            )
            return

        try:
            ruta_sel = self.combo_ruta.get()

            # -----------------------------------------------
            # FILTRAR ACTIVIDAD GPS POR RUTA Y UNIDADES
            # -----------------------------------------------
            if self.lector_actividad is not None:
                df_gps = (
                    self.lector_actividad.cargar_datos_completos(
                        ruta_sel
                    )
                )

                if df_gps is None or df_gps.empty:
                    self.df_actividad_gps = pd.DataFrame()

                else:
                    col_unidad = df_gps.columns[0]

                    unidades_normalizadas = {
                        str(u).replace("-", "").replace(" ", "").upper()
                        for u in unidades_sel
                    }

                    mascara = df_gps[col_unidad].apply(
                        lambda x: (
                            str(x).replace("-", "").replace(" ", "").upper()
                            in unidades_normalizadas
                        )
                    )

                    self.df_actividad_gps = (
                        df_gps.loc[mascara].reset_index(drop=True)
                    )

            # -----------------------------------------------
            # ANALIZAR GEOCERCAS
            # -----------------------------------------------
            df_unidades = (
                self.lector_geocercas.obtener_datos_unidades(
                    unidades_sel
                )
            )

            df_resultado = RutaService.analizar_unidades(
                df_unidades,
                tiempos_objetivo=self._obtener_tiempos_objetivo(),
                nombre_ruta=ruta_sel
            )

            if df_resultado is None or df_resultado.empty:
                messagebox.showwarning(
                    "Sin resultados",
                    "No se generaron resultados para las unidades seleccionadas."
                )
                return

            self.df_resultado_actual = df_resultado.copy()

            # -----------------------------------------------
            # RESUMEN DIARIO Y RESUMEN GENERAL
            # -----------------------------------------------
            df_resumen_diario = (
                RutaService.obtener_resumen_diario_unidades(
                    df_unidades
                )
            )

            df_resumen_general = (
                ServicioResumenGeneral.preparar_resumen_general(
                    df_resumen_diario=df_resumen_diario,
                    df_resultado_geocercas=df_resultado,
                    df_actividad_gps=self.df_actividad_gps
                )
            )

            self.df_resumen_actual = df_resumen_general.copy()

            # -----------------------------------------------
            # ACTUALIZAR TODAS LAS VISTAS
            # -----------------------------------------------
            self.vista_resumen.cargar_datos(
                df_resumen_general,
                df_resultado
            )

            self.vista_detalle.cargar_datos(df_resultado)
            self.vista_graficas.cargar_datos(df_resultado)
            self.vista_gps.cargar_datos(self.df_actividad_gps)

            self.notebook.select(self.tab_gps)

            messagebox.showinfo(
                "Éxito",
                f"Análisis de [{ruta_sel}] completado correctamente."
            )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error en el análisis:\n{e}"
            )

    # ========================================================
    # EXPORTAR RESUMEN
    # ========================================================
    def exportar_resumen(self):
        if self.df_resumen_actual.empty:
            messagebox.showwarning(
                "Sin datos",
                "Primero debes ejecutar un análisis."
            )
            return

        archivo = filedialog.asksaveasfilename(
            title="Guardar resumen",
            defaultextension=".xlsx",
            initialfile="resumen_rutas.xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )

        if archivo:
            try:
                self.df_resumen_actual.to_excel(
                    archivo,
                    index=False
                )
                messagebox.showinfo(
                    "Exportación",
                    "El resumen se exportó correctamente."
                )
            except Exception as e:
                messagebox.showerror(
                    "Error al exportar",
                    str(e)
                )

    # ========================================================
    # EXPORTAR DETALLE
    # ========================================================
    def exportar_detalle(self):
        if self.df_resultado_actual.empty:
            messagebox.showwarning(
                "Sin datos",
                "Primero debes ejecutar un análisis."
            )
            return

        archivo = filedialog.asksaveasfilename(
            title="Guardar detalle",
            defaultextension=".xlsx",
            initialfile="detalle_rutas.xlsx",
            filetypes=[("Archivos Excel", "*.xlsx")]
        )

        if archivo:
            try:
                df_exportar = self.df_resultado_actual.copy()

                columnas_omitir = [
                    "Vuelta_Num",
                    "Sentido",
                    "Tipo",
                    "Evaluacion_Tiempo",
                    "Segundos_Retraso",
                    "Hora de Salida"
                ]

                columnas_exportar = [
                    columna
                    for columna in df_exportar.columns
                    if columna not in columnas_omitir
                ]

                df_exportar[columnas_exportar].to_excel(
                    archivo,
                    index=False
                )

                messagebox.showinfo(
                    "Exportación",
                    "El detalle se exportó correctamente."
                )

            except Exception as e:
                messagebox.showerror(
                    "Error al exportar",
                    str(e)
                )


if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()
