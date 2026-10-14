# interfaz/vista_resumen_general.py
import re
import tkinter as tk
from tkinter import ttk
import pandas as pd
from configuracion.colores import PaletaColores


class VistaResumenGeneral(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.COLOR_BG = PaletaColores.BG_PRINCIPAL
        self.COLOR_PANEL = PaletaColores.PANEL_LATERAL
        self.COLOR_PRIMARY = PaletaColores.AZUL_COBALTO
        self.COLOR_TEXT_DARK = PaletaColores.TEXTO_OSCURO

        self.configure(style="Main.TFrame")
        self._configurar_estilos_treeview()
        self._crear_layout()

    def _configurar_estilos_treeview(self):
        style = ttk.Style(self)

        style.configure(
            "ResumenFlota.Treeview.Heading",
            background=self.COLOR_PANEL,
            foreground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            padding=6,
        )
        style.configure(
            "ResumenFlota.Treeview",
            background="#FFFFFF",
            foreground=self.COLOR_TEXT_DARK,
            fieldbackground="#FFFFFF",
            rowheight=26,
            font=("Segoe UI", 9),
        )
        style.map(
            "ResumenFlota.Treeview",
            background=[("selected", self.COLOR_PRIMARY)],
            foreground=[("selected", "#FFFFFF")],
        )

    def _crear_layout(self):
        frame_kpi = tk.Frame(self, bg=self.COLOR_PANEL, padx=12, pady=10)
        frame_kpi.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            frame_kpi,
            text="📊 RESUMEN GENERAL ",
            bg=self.COLOR_PANEL,
            fg="#38BDF8",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        grid_kpi = tk.Frame(frame_kpi, bg=self.COLOR_PANEL)
        grid_kpi.pack(anchor="w", fill="none")

        self.lbl_kpi_unidades = self._crear_kpi_card(
            grid_kpi, "CANTIDAD DE UNIDADES ANALIZADAS", "0", 0, 0, "#38BDF8"
        )

        frame_tabla = tk.Frame(self, bg=self.COLOR_BG)
        frame_tabla.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        cols = (
            "Unidad",
            "Hora_Inicio",
            "Hora_Termino",
            "Duracion_Ruta",
            "Retrasos",
            "Adelantos",
            "Omisiones",
            "Km_Actividad_Diaria",
            "Vel_Max_GPS",
            "Tiempo_en_Viajes",
        )

        self.tree = ttk.Treeview(
            frame_tabla,
            columns=cols,
            show="headings",
            style="ResumenFlota.Treeview",
        )

        nombres_cabecera = {
            "Unidad": "Unidad",
            "Hora_Inicio": "Hora Inicio",
            "Hora_Termino": "Hora Término",
            "Duracion_Ruta": "Tiempo Total",
            "Retrasos": "Retrasos",
            "Adelantos": "Adelantos",
            "Omisiones": "Omisiones",
            "Km_Actividad_Diaria": "Km Mensajes",
            "Vel_Max_GPS": "Velocidad Máx.",
            "Tiempo_en_Viajes": "Tiempo Viajes ",
        }

        for c in cols:
            self.tree.heading(c, text=nombres_cabecera.get(c, c))

        self.tree.column("Unidad", width=110, anchor="center")
        self.tree.column("Hora_Inicio", width=150, anchor="center")
        self.tree.column("Hora_Termino", width=150, anchor="center")
        self.tree.column("Duracion_Ruta", width=110, anchor="center")
        self.tree.column("Retrasos", width=80, anchor="center")
        self.tree.column("Adelantos", width=80, anchor="center")
        self.tree.column("Omisiones", width=80, anchor="center")
        self.tree.column("Km_Actividad_Diaria", width=140, anchor="center")
        self.tree.column("Vel_Max_GPS", width=110, anchor="center")
        self.tree.column("Tiempo_en_Viajes", width=130, anchor="center")

        scroll_y = ttk.Scrollbar(
            frame_tabla, orient="vertical", command=self.tree.yview
        )
        scroll_x = ttk.Scrollbar(
            frame_tabla, orient="horizontal", command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set
        )

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

    def _crear_kpi_card(
        self, parent, titulo, valor_def, row, col, color_val=None
    ):
        card = tk.Frame(parent, bg="#0F172A", padx=15, pady=8)
        card.grid(row=row, column=col, padx=4, pady=3, sticky="w")

        tk.Label(
            card,
            text=titulo,
            bg="#0F172A",
            fg="#94A3B8",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")

        lbl_v = tk.Label(
            card,
            text=valor_def,
            bg="#0F172A",
            fg=color_val if color_val else "#FFFFFF",
            font=("Segoe UI", 12, "bold"),
        )
        lbl_v.pack(anchor="w", pady=(2, 0))
        return lbl_v

    @staticmethod
    def _extraer_clave_unidad(txt) -> str:
        if not txt or pd.isna(txt):
            return ""
        txt_str = str(txt).strip().upper()
        match = re.search(r"([A-Z0-9]+)", txt_str)
        return match.group(1) if match else txt_str

    def cargar_datos(
        self,
        df_resultado: pd.DataFrame,
        df_resumen_diario: pd.DataFrame = None,
        df_actividad: pd.DataFrame = None,
    ):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df_resultado is None or df_resultado.empty:
            self.lbl_kpi_unidades.config(text="0")
            return

        unidades_analizadas = df_resultado["Agrupación"].unique().tolist()
        self.lbl_kpi_unidades.config(text=str(len(unidades_analizadas)))

        mapa_actividad = {}
        if df_actividad is not None and not df_actividad.empty:
            cols = list(df_actividad.columns)
            
            col_unid = cols[0]
            
            # DETECCIÓN DE COLUMNAS SEGÚN SU POSICIÓN O NOMBRE EXACTO EN TU EXCEL:
            # Columna 2: Kilometraje en todos los mensajes
            col_km = next(
                (c for c in cols if "TODOS LOS MENSAJE" in c.upper() or "TODOS LOS MENSAJES" in c.upper()),
                cols[2] if len(cols) > 2 else None
            )

            # Columna 4: Velocidad máxima
            col_vel = next(
                (c for c in cols if "MÁXIMA" in c.upper() or "MAXIMA" in c.upper()),
                cols[4] if len(cols) > 4 else None
            )

            # Columna 6: Tiempo en viajes (Se salta Horas de Motor que es la 5)
            col_gps = next(
                (c for c in cols if "TIEMPO EN VIAJES" in c.upper() or "TIEMPO DE VIAJE" in c.upper()),
                cols[6] if len(cols) > 6 else None
            )

            for _, row_act in df_actividad.iterrows():
                u_raw = row_act.get(col_unid)
                key_norm = self._extraer_clave_unidad(u_raw)

                if not key_norm:
                    continue

                km_val = str(row_act.get(col_km, "-")).strip() if col_km and pd.notna(row_act.get(col_km)) else "-"

                vel_raw = row_act.get(col_vel, "-") if col_vel and pd.notna(row_act.get(col_vel)) else "-"
                if vel_raw != "-":
                    try:
                        vel_val = str(int(float(vel_raw)))
                    except ValueError:
                        vel_val = str(vel_raw).strip()
                else:
                    vel_val = "-"

                gps_val = str(row_act.get(col_gps, "-")).strip() if col_gps and pd.notna(row_act.get(col_gps)) else "-"

                mapa_actividad[key_norm] = {
                    "km_actividad": km_val,
                    "vel_max": vel_val,
                    "tiempo_viajes": gps_val,
                }

        for unidad_id in unidades_analizadas:
            df_u = df_resultado[df_resultado["Agrupación"] == unidad_id]

            cant_retrasos = 0
            cant_adelantos = 0
            cant_omisiones = 0

            for _, row in df_u.iterrows():
                eval_t = str(row.get("Evaluacion_Tiempo", ""))
                estado = str(row.get("Estado_Ruta", ""))
                tipo = str(row.get("Tipo", ""))

                if "Dif: +" in eval_t:
                    cant_retrasos += 1
                elif "Dif: -" in eval_t:
                    cant_adelantos += 1

                if "NO REGISTRADA" in estado or "Omitida" in tipo or "Faltante" in str(row.get("Geocerca", "")):
                    cant_omisiones += 1

            h_inicio = "-"
            h_termino = "-"
            t_total = "-"

            if df_resumen_diario is not None and not df_resumen_diario.empty:
                df_res_u = df_resumen_diario[df_resumen_diario["Agrupación"] == unidad_id]
                if not df_res_u.empty:
                    row_r = df_res_u.iloc[0]
                    h_inicio = str(row_r.get("Hora_Inicio", "-"))
                    h_termino = str(row_r.get("Hora_Termino", "-"))
                    t_total = str(row_r.get("Tiempo_Total", "-"))

            key_norm = self._extraer_clave_unidad(unidad_id)
            d_act = mapa_actividad.get(
                key_norm,
                {
                    "km_actividad": "-",
                    "vel_max": "-",
                    "tiempo_viajes": "-",
                },
            )

            valores = (
                str(unidad_id),
                h_inicio,
                h_termino,
                t_total,
                str(cant_retrasos),
                str(cant_adelantos),
                str(cant_omisiones),
                d_act["km_actividad"],   # 128.33 km
                d_act["vel_max"],        # 39 km/h
                d_act["tiempo_viajes"],  # 9:35:17
            )
            self.tree.insert("", "end", values=valores)

    def obtener_dataframe_exportable(self) -> pd.DataFrame:
        filas = []
        for child in self.tree.get_children():
            filas.append(self.tree.item(child)["values"])
        cols = [
            "Unidad", "Hora Inicio", "Hora Término", "Tiempo Total",
            "Retrasos", "Adelantos", "Omisiones", "Km Actividad Diaria",
            "Velocidad Máx.", "Tiempo Viajes GPS"
        ]
        return pd.DataFrame(filas, columns=cols)