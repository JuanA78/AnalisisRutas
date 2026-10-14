# main.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd

from configuracion.colores import PaletaColores
from configuracion.rutas_config import RutasConfig
from interfaz.vista_actividad_diaria import VistaActividadDiaria
from interfaz.vista_grafica_individual import VistaGraficaIndividual
from interfaz.vista_resumen_general import VistaResumenGeneral
from interfaz.vista_tabla_individual import VistaTablaIndividual
from servicios.actividad_service import ActividadService
from servicios.analiticos_service import AnaliticosService
from servicios.ruta_service import RutaService
from servicios.unidades_service import UnidadesService


class VentanaPrincipal(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Analizador de Rutas 3000")
        self.geometry("1350x780")
        self.minsize(1100, 680)

        self.configure(bg=PaletaColores.BG_PRINCIPAL)

        self.unidades_service = None
        self.actividad_service = None
        self.df_resultado_actual = None
        self.entries_tiempos = {}

        self._configurar_estilos_ttk()
        self._crear_interfaz()

    def _configurar_estilos_ttk(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Main.TNotebook",
            background=PaletaColores.BG_PRINCIPAL,
            borderwidth=0,
        )
        style.configure(
            "Main.TNotebook.Tab",
            background="#E2E8F0",
            foreground=PaletaColores.TEXTO_OSCURO,
            font=("Segoe UI", 9, "bold"),
            padding=(15, 8),
            borderwidth=0,
        )
        style.map(
            "Main.TNotebook.Tab",
            background=[("selected", PaletaColores.AZUL_COBALTO)],
            foreground=[("selected", "#FFFFFF")],
        )

        style.configure("Main.TFrame", background=PaletaColores.BG_PRINCIPAL)

        style.configure(
            "Sidebar.TLabelframe",
            background=PaletaColores.PANEL_LATERAL,
            foreground=PaletaColores.TEXTO_BLANCO,
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Sidebar.TLabelframe.Label",
            background=PaletaColores.PANEL_LATERAL,
            foreground=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 9, "bold"),
        )

    def _crear_interfaz(self):
        panel_izq = tk.Frame(
            self, bg=PaletaColores.PANEL_LATERAL, width=320, padx=15, pady=15
        )
        panel_izq.pack(side="left", fill="y")
        panel_izq.pack_propagate(False)

        lbl_titulo = tk.Label(
            panel_izq,
            text="⚙️ PANEL CONTROL",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 12, "bold"),
        )
        lbl_titulo.pack(anchor="w", pady=(0, 12))

        btn_cargar_geocercas = tk.Button(
            panel_izq,
            text="📂 Cargar Geocercas (Excel)",
            bg=PaletaColores.AZUL_OCEANO,
            fg=PaletaColores.TEXTO_BLANCO,
            activebackground="#0369A1",
            activeforeground=PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6,
            command=self.cargar_excel_geocercas,
        )
        btn_cargar_geocercas.pack(fill="x", pady=(0, 6))

        btn_cargar_actividad = tk.Button(
            panel_izq,
            text="📂 Cargar Actividad GPS (Excel)",
            bg=PaletaColores.AZUL_OCEANO,
            fg=PaletaColores.TEXTO_BLANCO,
            activebackground="#0369A1",
            activeforeground=PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            pady=6,
            command=self.cargar_excel_actividad,
        )
        btn_cargar_actividad.pack(fill="x", pady=(0, 10))

        # BOTONES DE EXPORTACIÓN A EXCEL
        frame_export = tk.Frame(panel_izq, bg=PaletaColores.PANEL_LATERAL)
        frame_export.pack(fill="x", pady=(0, 12))

        btn_exp_resumen = tk.Button(
            frame_export,
            text="📗 Exp. Resumen Excel",
            bg="#059669",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            pady=5,
            command=self.exportar_resumen_excel,
        )
        btn_exp_resumen.pack(side="left", fill="x", expand=True, padx=(0, 2))

        btn_exp_detalle = tk.Button(
            frame_export,
            text="📗 Exp. Detalle Excel",
            bg="#059669",
            fg="#FFFFFF",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            cursor="hand2",
            pady=5,
            command=self.exportar_detalle_excel,
        )
        btn_exp_detalle.pack(side="right", fill="x", expand=True, padx=(2, 0))

        tk.Label(
            panel_izq,
            text="Seleccionar Ruta:",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.TEXTO_MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        self.cb_ruta = ttk.Combobox(
            panel_izq,
            values=["El Arbolito", "Agua Salada"],
            state="readonly",
            font=("Segoe UI", 9),
        )
        self.cb_ruta.current(0)
        self.cb_ruta.pack(fill="x", pady=(3, 10))
        self.cb_ruta.bind("<<ComboboxSelected>>", self._al_cambiar_ruta)

        tk.Label(
            panel_izq,
            text="Unidades a Analizar:",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.TEXTO_MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        frame_listbox = tk.Frame(
            panel_izq, bg=PaletaColores.BORDE_SUAVE, bd=1
        )
        frame_listbox.pack(fill="x", pady=(3, 10))

        self.listbox_unidades = tk.Listbox(
            frame_listbox,
            selectmode="multiple",
            exportselection=False,
            height=4,
            bg=PaletaColores.CARD_OSCURA,
            fg="#F8FAFC",
            selectbackground=PaletaColores.AZUL_COBALTO,
            selectforeground="#FFFFFF",
            font=("Consolas", 9),
            border=0,
            highlightthickness=0,
        )
        scroll_lb = tk.Scrollbar(
            frame_listbox,
            orient="vertical",
            command=self.listbox_unidades.yview,
        )
        self.listbox_unidades.configure(yscrollcommand=scroll_lb.set)
        scroll_lb.pack(side="right", fill="y")
        self.listbox_unidades.pack(side="left", fill="both", expand=True)

        self.frame_tiempos = ttk.LabelFrame(
            panel_izq,
            text=" Configuración Tiempos (Min) ",
            style="Sidebar.TLabelframe",
            padding=8,
        )
        self.frame_tiempos.pack(fill="x", pady=(0, 10))

        self._construir_campos_tiempos()

        btn_analizar = tk.Button(
            panel_izq,
            text="⚡ ANALIZAR SELECCIONADAS",
            bg=PaletaColores.AZUL_COBALTO,
            fg=PaletaColores.TEXTO_BLANCO,
            activebackground="#1D4ED8",
            activeforeground=PaletaColores.TEXTO_BLANCO,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self.ejecutar_analisis,
        )
        btn_analizar.pack(fill="x", side="bottom")

        self.notebook = ttk.Notebook(self, style="Main.TNotebook")
        self.notebook.pack(
            side="right", fill="both", expand=True, padx=12, pady=12
        )

        self.vista_resumen = VistaResumenGeneral(self.notebook)
        self.notebook.add(self.vista_resumen, text="📊 Resumen General Exec")

        self.vista_tabla = VistaTablaIndividual(self.notebook)
        self.notebook.add(self.vista_tabla, text="📋 Registros por Unidad")

        self.vista_grafica = VistaGraficaIndividual(self.notebook)
        self.notebook.add(self.vista_grafica, text="📈 Visualización de Gráficas")

        self.vista_actividad = VistaActividadDiaria(self.notebook)
        self.notebook.add(self.vista_actividad, text="📑 Actividad Diaria GPS")

    def _construir_campos_tiempos(self):
        for widget in self.frame_tiempos.winfo_children():
            widget.destroy()

        self.entries_tiempos.clear()
        ruta_sel = self.cb_ruta.get()

        if "Agua Salada" in ruta_sel:
            tramos_ida = [
                ("Canal_CasaEloy ➔ Centro", ("Canal_CasaEloy", "Centro"), 9),
                ("Centro ➔ Polo Norte", ("Centro", "Polo Norte"), 6),
                ("Polo Norte ➔ Iberia", ("Polo Norte", "Iberia"), 5),
                ("Iberia ➔ AguaSalada", ("Iberia", "AguaSalada"), 11),
            ]
            tramos_vuelta = [
                ("AguaSalada ➔ Iberia", ("AguaSalada", "Iberia"), 5),
                ("Iberia ➔ Polo Norte", ("Iberia", "Polo Norte"), 5),
                ("Polo Norte ➔ Centro", ("Polo Norte", "Centro"), 10),
                ("Centro ➔ Canal_CasaEloy", ("Centro", "Canal_CasaEloy"), 12),
            ]
        else:
            tramos_ida = [
                ("La Cruz ➔ Centro", ("La Cruz", "Centro"), 17),
                ("Centro ➔ Polo Norte", ("Centro", "Polo Norte"), 8),
                ("Polo Norte ➔ Iberia", ("Polo Norte", "Iberia"), 5),
                ("Iberia ➔ CTM", ("Iberia", "CTM"), 13),
                ("CTM ➔ Gavilan", ("CTM", "Gavilan"), 10),
            ]
            tramos_vuelta = [
                ("Gavilan ➔ CTM", ("Gavilan", "CTM"), 10),
                ("CTM ➔ Iberia", ("CTM", "Iberia"), 3),
                ("Iberia ➔ Polo Norte", ("Iberia", "Polo Norte"), 5),
                ("Polo Norte ➔ Centro", ("Polo Norte", "Centro"), 12),
                ("Centro ➔ La Cruz", ("Centro", "La Cruz"), 19),
            ]

        tk.Label(
            self.frame_tiempos,
            text="— IDA —",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")

        for label_text, key, val_def in tramos_ida:
            f = tk.Frame(self.frame_tiempos, bg=PaletaColores.PANEL_LATERAL)
            f.pack(fill="x", pady=1)
            tk.Label(
                f,
                text=label_text,
                bg=PaletaColores.PANEL_LATERAL,
                fg=PaletaColores.TEXTO_BLANCO,
                font=("Segoe UI", 8),
                width=20,
                anchor="w",
            ).pack(side="left")
            ent = tk.Entry(
                f,
                width=5,
                bg=PaletaColores.CARD_OSCURA,
                fg="#FFFFFF",
                insertbackground="#FFFFFF",
                relief="flat",
                bd=1,
            )
            ent.insert(0, str(val_def))
            ent.pack(side="right")
            self.entries_tiempos[key] = ent

        tk.Label(
            self.frame_tiempos,
            text="— VUELTA —",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.CELESTE_VIBRANTE,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(4, 0))

        for label_text, key, val_def in tramos_vuelta:
            f = tk.Frame(self.frame_tiempos, bg=PaletaColores.PANEL_LATERAL)
            f.pack(fill="x", pady=1)
            tk.Label(
                f,
                text=label_text,
                bg=PaletaColores.PANEL_LATERAL,
                fg=PaletaColores.TEXTO_BLANCO,
                font=("Segoe UI", 8),
                width=20,
                anchor="w",
            ).pack(side="left")
            ent = tk.Entry(
                f,
                width=5,
                bg=PaletaColores.CARD_OSCURA,
                fg="#FFFFFF",
                insertbackground="#FFFFFF",
                relief="flat",
                bd=1,
            )
            ent.insert(0, str(val_def))
            ent.pack(side="right")
            self.entries_tiempos[key] = ent

    def _al_cambiar_ruta(self, event=None):
        self._construir_campos_tiempos()
        self._preseleccionar_unidades_por_ruta()

    def _preseleccionar_unidades_por_ruta(self):
        ruta_sel = self.cb_ruta.get()
        self.listbox_unidades.selection_clear(0, tk.END)

        for i in range(self.listbox_unidades.size()):
            unidad_item = self.listbox_unidades.get(i)
            ruta_detectada = RutasConfig.obtener_ruta_predeterminada(unidad_item)
            if ruta_detectada == ruta_sel:
                self.listbox_unidades.selection_set(i)

    def cargar_excel_geocercas(self):
        path = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if not path:
            return

        try:
            self.unidades_service = UnidadesService(path)
            unidades = self.unidades_service.obtener_unidades()

            self.listbox_unidades.delete(0, tk.END)
            for u in unidades:
                self.listbox_unidades.insert(tk.END, u)

            self._preseleccionar_unidades_por_ruta()

            messagebox.showinfo(
                "Éxito",
                f"Se cargaron {len(unidades)} unidades del archivo de Geocercas.",
            )
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo cargar el archivo de Geocercas: {e}"
            )

    def cargar_excel_actividad(self):
        path = filedialog.askopenfilename(
            filetypes=[("Archivos Excel", "*.xlsx *.xls")]
        )
        if not path:
            return

        try:
            self.actividad_service = ActividadService(path)
            df_act = self.actividad_service.cargar_datos()
            total_unidades = len(df_act) if df_act is not None else 0

            self.vista_actividad.cargar_datos(df_act)

            messagebox.showinfo(
                "Éxito",
                f"Se cargaron {total_unidades} registros de Actividad GPS.",
            )
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo cargar el archivo de Actividad GPS: {e}",
            )

    def exportar_resumen_excel(self):
        df_exp = self.vista_resumen.obtener_dataframe_exportable()
        if df_exp.empty:
            messagebox.showwarning("Atención", "No hay datos en el Resumen General para exportar.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="Resumen_General.xlsx"
        )
        if path:
            df_exp.to_excel(path, index=False)
            messagebox.showinfo("Éxito", f"Resumen General exportado correctamente a:\n{path}")

    # main.py

    # main.py -> actualizar exportar_detalle_excel()

    def exportar_detalle_excel(self):
        if self.df_resultado_actual is None or self.df_resultado_actual.empty:
            messagebox.showwarning(
                "Atención", "Ejecuta un análisis primero para exportar el detalle."
            )
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="Registros_Detalle_Unidades.xlsx",
        )
        if path:
            # Columnas internas que se ocultarán/excluirán de la exportación a Excel
            columnas_a_ocultar = [
                "Vuelta_Num",
                "Sentido",
                "Tipo",
                "Evaluacion_Tiempo",
                "Hora de salida",
            ]

            # Filtrar el DataFrame excluyendo las columnas seleccionadas
            df_exportar = self.df_resultado_actual.drop(
                columns=[col for col in columnas_a_ocultar if col in self.df_resultado_actual.columns],
                errors="ignore",
            )


            # Exportar archivo limpio a Excel
            df_exportar.to_excel(path, index=False)

            messagebox.showinfo(
                "Éxito",
                f"Detalle de Unidades exportado correctamente (con vista limpia) a:\n{path}",
            )
            
    def obtener_tiempos_configurados(self):
        tiempos = {}
        for key, entry in self.entries_tiempos.items():
            val = entry.get().strip()
            try:
                tiempos[key] = float(val) if val else 0.0
            except ValueError:
                tiempos[key] = 0.0
        return tiempos

    def ejecutar_analisis(self):
        if not self.unidades_service:
            messagebox.showwarning(
                "Atención", "Carga primero el archivo Excel de Geocercas."
            )
            return

        indices = self.listbox_unidades.curselection()
        if not indices:
            messagebox.showwarning(
                "Atención", "Selecciona al menos una unidad de la lista."
            )
            return

        unidades_sel = [self.listbox_unidades.get(i) for i in indices]
        tiempos_custom = self.obtener_tiempos_configurados()

        df_unidades = self.unidades_service.obtener_datos_unidades(
            unidades_sel
        )

        es_semanal = AnaliticosService.es_reporte_semanal(df_unidades)

        df_actividad = (
            self.actividad_service.df
            if self.actividad_service
            else pd.DataFrame()
        )

        self.df_resultado_actual = RutaService.analizar_unidades(
            df_unidades, tiempos_objetivo=tiempos_custom
        )
        df_resumen_diario = RutaService.obtener_resumen_diario_unidades(
            df_unidades
        )

        self.vista_resumen.cargar_datos(
            df_resultado=self.df_resultado_actual,
            df_resumen_diario=df_resumen_diario,
            df_actividad=df_actividad,
        )
        self.vista_tabla.cargar_datos(self.df_resultado_actual)
        self.vista_grafica.cargar_datos(self.df_resultado_actual, es_semanal=es_semanal)
        self.vista_actividad.cargar_datos(df_actividad)


if __name__ == "__main__":
    app = VentanaPrincipal()
    app.mainloop()