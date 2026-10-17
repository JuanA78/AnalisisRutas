import tkinter as tk
from tkinter import ttk
import unicodedata
import pandas as pd

from configuracion.colores import PaletaColores


class VistaActividadGeocercas(ttk.Frame):
    """Vista para consultar la actividad de geocercas por unidad."""

    def __init__(self, parent):
        super().__init__(parent)
        self.df_resultado = pd.DataFrame()
        self.configure(style="Main.TFrame")
        self._crear_layout()

    @staticmethod
    def _normalizar(valor):
        texto = str(valor if valor is not None else "").strip().upper()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        return texto

    @staticmethod
    def _limpiar_valor(valor):
        if valor is None:
            return "-"
        try:
            if pd.isna(valor):
                return "-"
        except (TypeError, ValueError):
            pass

        texto = str(valor).strip()
        if texto.lower() in ("", "nan", "nat", "none"):
            return "-"
        return texto

    @staticmethod
    def _obtener_columna(df, *nombres):
        columnas = {
            VistaActividadGeocercas._normalizar(col): col
            for col in df.columns
        }
        for nombre in nombres:
            clave = VistaActividadGeocercas._normalizar(nombre)
            if clave in columnas:
                return columnas[clave]
        return None

    def _crear_layout(self):
        frame_top = tk.Frame(
            self,
            bg=PaletaColores.PANEL_LATERAL,
            padx=12,
            pady=10,
        )
        frame_top.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            frame_top,
            text="Seleccionar unidad:",
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
        self.cb_unidades.bind("<<ComboboxSelected>>", self._al_seleccionar_unidad)

        self.lbl_total_regs = tk.Label(
            frame_top,
            text="0 registros procesados",
            bg=PaletaColores.PANEL_LATERAL,
            fg=PaletaColores.TEXTO_MUTED,
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_total_regs.pack(side="right")

        frame_tabla = tk.Frame(
            self,
            bg=PaletaColores.BG_PRINCIPAL,
        )
        frame_tabla.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(5, 10),
        )

        self.columnas = (
            "Agrupación",
            "Geocerca",
            "Entrada",
            "Salida",
            "Tiempo_Real",
            "Tiempo_Estimado",
            "Desfase",
            "Estado_Ruta",
        )

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=self.columnas,
            show="headings",
            height=18,
        )

        encabezados = {
            "Agrupación": "Unidad",
            "Geocerca": "Geocerca",
            "Entrada": "Entrada",
            "Salida": "Salida",
            "Tiempo_Real": "Tiempo real",
            "Tiempo_Estimado": "Tiempo estimado",
            "Desfase": "Desfase",
            "Estado_Ruta": "Estado de ruta",
        }

        anchos = {
            "Agrupación": 90,
            "Geocerca": 190,
            "Entrada": 130,
            "Salida": 130,
            "Tiempo_Real": 115,
            "Tiempo_Estimado": 125,
            "Desfase": 110,
            "Estado_Ruta": 155,
        }

        for columna in self.columnas:
            self.tree.heading(columna, text=encabezados[columna])
            self.tree.column(
                columna,
                width=anchos[columna],
                minwidth=75,
                anchor="center",
                stretch=True,
            )

        # Configuración de Colores de Etiquetas
        self.tree.tag_configure("atiempo", background="#DCFCE7", foreground="#166534")
        self.tree.tag_configure("adelanto", background="#FEF3C7", foreground="#92400E")
        self.tree.tag_configure("retraso", background="#FEE2E2", foreground="#991B1B")
        self.tree.tag_configure("no_registrada", background="#DBEAFE", foreground="#1D4ED8")
        self.tree.tag_configure("corte", background="#EDE9FE", foreground="#6D28D9")  # Morado destacado para cortes
        self.tree.tag_configure("reinicio", background="#334155", foreground="#F8FAFC")
        self.tree.tag_configure("repetida", background="#F1F5F9", foreground="#475569")
        self.tree.tag_configure("neutral", background="#FFFFFF", foreground="#0F172A")

        scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    def cargar_datos(self, df_resultado: pd.DataFrame):
        self.df_resultado = (
            df_resultado.copy() if df_resultado is not None else pd.DataFrame()
        )

        self._limpiar_tabla()

        if self.df_resultado.empty:
            self.cb_unidades["values"] = ()
            self.cb_unidades.set("")
            self.lbl_total_regs.config(text="0 registros procesados")
            return

        col_unidad = self._obtener_columna(
            self.df_resultado, "Agrupación", "Agrupacion"
        )

        if col_unidad is None:
            self.cb_unidades["values"] = ()
            self.cb_unidades.set("")
            self.lbl_total_regs.config(text="Falta la columna Agrupación")
            return

        self._col_unidad = col_unidad

        unidades = (
            self.df_resultado[col_unidad]
            .dropna()
            .astype(str)
            .str.strip()
        )
        unidades = sorted(
            unidades[unidades != ""].unique().tolist(),
            key=str.casefold,
        )

        self.cb_unidades["values"] = unidades

        if unidades:
            self.cb_unidades.current(0)
            self._al_seleccionar_unidad()
        else:
            self.cb_unidades.set("")
            self.lbl_total_regs.config(text="0 registros procesados")

    def _limpiar_tabla(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    @staticmethod
    def _obtener_color(estado_ruta, evaluacion_tiempo, tipo, geocerca=""):
        estado = VistaActividadGeocercas._normalizar(estado_ruta)
        evaluacion = VistaActividadGeocercas._normalizar(evaluacion_tiempo)
        tipo_n = VistaActividadGeocercas._normalizar(tipo)
        geo = VistaActividadGeocercas._normalizar(geocerca)

        geo_compacta = geo.replace(" ", "").replace("_", "").replace("-", "")

        # 1. Cortes tienen prioridad visual morada
        es_corte = (
            "CORTE" in estado
            or tipo_n == "CORTE"
            or "CORTEIMSS" in geo_compacta
            or "CENTRALDEAUTOBUSES" in geo_compacta
        )
        if es_corte:
            return "corte"

        # 2. Geocercas no registradas / faltantes
        if "NO REGISTRADA" in estado or "FALTANTE" in geo or tipo_n == "OMITIDA":
            return "no_registrada"

        # 3. Reinicio de ruta
        if "REINICIO" in estado or "REINICIO" in tipo_n:
            return "reinicio"

        # 4. Geocercas repetidas
        if "REPETIDA" in estado or "REPETIDA" in tipo_n:
            return "repetida"

        # 5. Evaluación temporal
        if "RETRASO" in evaluacion:
            return "retraso"
        if "ADELANTO" in evaluacion:
            return "adelanto"
        if "A TIEMPO" in evaluacion:
            return "atiempo"

        return "neutral"

    def _al_seleccionar_unidad(self, event=None):
        unidad = self.cb_unidades.get()

        if not unidad or self.df_resultado.empty:
            self._limpiar_tabla()
            self.lbl_total_regs.config(text="0 registros procesados")
            return

        col_unidad = getattr(
            self,
            "_col_unidad",
            self._obtener_columna(self.df_resultado, "Agrupación", "Agrupacion"),
        )

        if col_unidad is None:
            self._limpiar_tabla()
            self.lbl_total_regs.config(text="Falta la columna de unidad")
            return

        self._limpiar_tabla()

        mascara = (
            self.df_resultado[col_unidad]
            .astype(str)
            .str.strip()
            == unidad
        )

        df_unidad = self.df_resultado.loc[mascara]
        self.lbl_total_regs.config(
            text=f"{len(df_unidad)} registros procesados"
        )

        col_estado = self._obtener_columna(df_unidad, "Estado_Ruta", "Estado Ruta")
        col_eval = self._obtener_columna(df_unidad, "Evaluacion_Tiempo", "Evaluacion Tiempo")
        col_tipo = self._obtener_columna(df_unidad, "Tipo")
        col_geo = self._obtener_columna(df_unidad, "Geocerca")

        for _, fila in df_unidad.iterrows():
            estado = fila.get(col_estado, "-") if col_estado else "-"
            evaluacion = fila.get(col_eval, "-") if col_eval else "-"
            tipo = fila.get(col_tipo, "-") if col_tipo else "-"
            geocerca = fila.get(col_geo, "-") if col_geo else "-"

            color = self._obtener_color(
                estado_ruta=estado,
                evaluacion_tiempo=evaluacion,
                tipo=tipo,
                geocerca=geocerca,
            )

            valores = []
            for columna in self.columnas:
                col_real = self._obtener_columna(self.df_resultado, columna)
                if col_real is None and columna == "Agrupación":
                    col_real = col_unidad

                valor = fila.get(col_real, "-") if col_real is not None else "-"
                valores.append(self._limpiar_valor(valor))

            self.tree.insert(
                "",
                "end",
                values=tuple(valores),
                tags=(color,),
            )