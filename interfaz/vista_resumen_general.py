import tkinter as tk
from tkinter import ttk
import pandas as pd

from configuracion.colores import PaletaColores
from servicios.servicio_resumen_general import ServicioResumenGeneral


class VistaResumenGeneral(tk.Frame):
    """
    Vista de Resumen Ejecutivo con el mismo estilo visual que Actividad Diaria GPS
    (#0F172A en encabezados) y panel desplegable con los Top 5 mayores retrasos por unidad.
    """

    COLOR_ENCABEZADO_BG = "#0F172A"

    COLUMNAS = [
        ("Unidad", "Unidad", 90),
        ("Hora Inicio", "Hora Inicio", 120),
        ("Hora Término", "Hora Término", 120),
        ("Tiempo Total", "Tiempo Total", 110),
        ("A Tiempo", "A Tiempo", 80),
        ("Retrasos", "Retrasos", 80),
        ("Adelantos", "Adelantos", 80),
        ("Omisiones", "Omisiones", 80),
        ("Km Actividad Diaria", "Km Mensajes", 130),
        ("Velocidad Máx.", "Velocidad Máx.", 110),
        ("Tiempo Viajes GPS", "Tiempo Viajes", 130),
    ]

    def __init__(self, parent):
        super().__init__(parent, bg=getattr(PaletaColores, "BG_PRINCIPAL", "#0F172A"))

        self.df_resultado = pd.DataFrame()
        self.df_resumen = pd.DataFrame()

        self._crear_interfaz()

    def _crear_interfaz(self):
        # ---------------------------------------------------------------------
        # 1. ENCABEZADO Y TARJETA MÉTRICA
        # ---------------------------------------------------------------------
        frame_top = tk.Frame(
            self,
            bg=getattr(PaletaColores, "BG_PRINCIPAL", "#0F172A"),
            pady=10,
            padx=10,
        )
        frame_top.pack(fill="x")

        card_qty = tk.Frame(
            frame_top,
            bg=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            bd=1,
            relief="solid",
        )
        card_qty.pack(side="left", padx=5)

        tk.Label(
            card_qty,
            text="CANTIDAD DE UNIDADES ANALIZADAS",
            bg=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            fg=getattr(PaletaColores, "CELESTE_VIBRANTE", "#38BDF8"),
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=10, pady=(5, 2))

        self.lbl_cant_unidades = tk.Label(
            card_qty,
            text="0",
            bg=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            fg="#FFFFFF",
            font=("Segoe UI", 14, "bold"),
        )
        self.lbl_cant_unidades.pack(anchor="w", padx=10, pady=(0, 5))

        # ---------------------------------------------------------------------
        # 2. CONFIGURACIÓN DE ESTILO IGUAL A ACTIVIDAD DIARIA GPS
        # ---------------------------------------------------------------------
        estilo = ttk.Style()

        # Estilo de las filas
        estilo.configure(
            "ResumenGPS.Treeview",
            background=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            foreground=getattr(PaletaColores, "TEXTO_BLANCO", "#FFFFFF"),
            fieldbackground=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            rowheight=28,
            font=("Segoe UI", 9),
        )

        estilo.map(
            "ResumenGPS.Treeview",
            background=[("selected", getattr(PaletaColores, "AZUL_OCEANO", "#0284C7"))],
            foreground=[("selected", getattr(PaletaColores, "TEXTO_BLANCO", "#FFFFFF"))],
        )

        # Estilo de Encabezados con fondo #0F172A
        estilo.configure(
            "ResumenGPS.Treeview.Heading",
            background=self.COLOR_ENCABEZADO_BG,
            foreground=getattr(PaletaColores, "CELESTE_VIBRANTE", "#38BDF8"),
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )

        estilo.map(
            "ResumenGPS.Treeview.Heading",
            background=[("active", getattr(PaletaColores, "CARD_BG", "#2A364F"))],
            foreground=[("active", getattr(PaletaColores, "TEXTO_BLANCO", "#FFFFFF"))],
        )

        # ---------------------------------------------------------------------
        # 3. TABLA CON BARRAS DE DESPLAZAMIENTO
        # ---------------------------------------------------------------------
        frame_tabla = tk.Frame(
            self,
            bg=getattr(PaletaColores, "BG_PRINCIPAL", "#0F172A"),
            padx=10,
            pady=5,
        )
        frame_tabla.pack(fill="both", expand=True)

        cols_ids = [c[0] for c in self.COLUMNAS]

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=cols_ids,
            show="headings",
            style="ResumenGPS.Treeview",
        )

        for cid, text, width in self.COLUMNAS:
            self.tree.heading(cid, text=text)
            self.tree.column(cid, width=width, anchor="center")

        # Tags para filas alternadas
        self.tree.tag_configure(
            "fila_par",
            background=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
        )
        self.tree.tag_configure(
            "fila_impar",
            background=getattr(PaletaColores, "CARD_BG", "#2A364F"),
        )

        sb_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # ---------------------------------------------------------------------
        # 4. PANEL INFERIOR DETALLE DE TOP 5 RETRASOS
        # ---------------------------------------------------------------------
        self.frame_detalles = tk.LabelFrame(
            self,
            text=" TOP 5 MAYORES RETRASOS REGISTRADOS ",
            bg=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            fg=getattr(PaletaColores, "CELESTE_VIBRANTE", "#38BDF8"),
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=8,
        )
        self.frame_detalles.pack(fill="x", padx=10, pady=(5, 10))

        self.lbl_top5 = tk.Label(
            self.frame_detalles,
            text="Selecciona una unidad en la tabla para consultar los 5 mayores retrasos (lugar, hora exacta y desfase).",
            bg=getattr(PaletaColores, "CARD_OSCURA", "#0F172A"),
            fg=getattr(PaletaColores, "TEXTO_MUTED", "#94A3B8"),
            font=("Segoe UI", 9),
            justify="left",
            anchor="w",
        )
        self.lbl_top5.pack(fill="x")

        # Evento de clic en la tabla
        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

    def cargar_datos(self, df_resumen: pd.DataFrame, df_resultado: pd.DataFrame = None):
        """Puebla la tabla de resumen y almacena df_resultado para consultar retrasos."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.df_resumen = df_resumen if df_resumen is not None else pd.DataFrame()
        self.df_resultado = df_resultado if df_resultado is not None else pd.DataFrame()

        if self.df_resumen.empty:
            self.lbl_cant_unidades.config(text="0")
            return

        self.lbl_cant_unidades.config(text=str(len(self.df_resumen)))

        for idx, row in self.df_resumen.iterrows():
            vals = []
            for cid, _, _ in self.COLUMNAS:
                val = row.get(cid, "-")
                if pd.isna(val) or str(val).strip() in ["nan", "None", ""]:
                    val = "-"
                vals.append(str(val))

            tag_fila = "fila_par" if idx % 2 == 0 else "fila_impar"
            self.tree.insert("", "end", values=vals, tags=(tag_fila,))

    def _al_seleccionar_fila(self, event=None):
        """Obtiene mediante el servicio los 5 retrasos más altos de la unidad seleccionada."""
        seleccion = self.tree.selection()
        if not seleccion:
            return

        item = self.tree.item(seleccion[0])
        valores = item.get("values", [])
        if not valores:
            return

        unidad_id = str(valores[0]).strip()

        # Consulta los retrasos a la capa de servicio
        top5 = ServicioResumenGeneral.obtener_top_5_retrasos_unidad(
            self.df_resultado, unidad_id
        )

        if not top5:
            self.lbl_top5.config(
                text=f"Unidad {unidad_id}: Sin retrasos significativos registrados.",
                fg=getattr(PaletaColores, "VERDE_EXITO", "#22C55E"),
            )
            return

        lineas = [f"Unidad {unidad_id} - Detalle de los 5 retrasos más altos:"]
        for i, det in enumerate(top5, 1):
            lineas.append(
                f"  {i}. Geocerca: {det['geocerca']} | Hora: {det['hora']} | Desfase: {det['desfase']}"
            )

        self.lbl_top5.config(
            text="\n".join(lineas),
            fg="#FFFFFF",
        )

    def cargar_datos_completos(
        self,
        df_actividad: pd.DataFrame,
        unidades: list = None,
        tiempos_geocercas: dict = None,
    ):
        """Compatibilidad para llamadas externas."""
        self.cargar_datos(df_actividad)