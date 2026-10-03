import tkinter as tk
from tkinter import ttk

class TablaResultados(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self._crear_tabla()

    def _crear_tabla(self):
        columnas = (
            "№", "Agrupación", "Geocerca", "Tipo", 
            "Hora de entrada", "Hora de salida", "Sentido", 
            "Estado_Ruta", "Tiempo_Min", "Evaluacion_Tiempo"
        )
        
        self.tree = ttk.Treeview(self, columns=columnas, show="headings")

        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)

        # Ajustes de ancho para columnas con más texto
        self.tree.column("Estado_Ruta", width=160, anchor="w")
        self.tree.column("Tiempo_Min", width=110, anchor="center")
        self.tree.column("Evaluacion_Tiempo", width=180, anchor="center")

        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def cargar_datos(self, df):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df is None or df.empty:
            return

        for _, row in df.iterrows():
            num = str(row.get("№", ""))
            agrupacion = str(row.get("Agrupación", ""))
            geocerca = str(row.get("Geocerca", ""))
            tipo = str(row.get("Tipo", ""))
            
            hora_in = row.get("Hora de entrada", "")
            hora_in_str = hora_in.strftime("%Y-%m-%d %H:%M:%S") if hasattr(hora_in, 'strftime') else str(hora_in)
            
            hora_out = row.get("Hora de salida", "")
            hora_out_str = hora_out.strftime("%Y-%m-%d %H:%M:%S") if hasattr(hora_out, 'strftime') else str(hora_out)
            
            sentido = str(row.get("Sentido", ""))
            estado = str(row.get("Estado_Ruta", ""))
            tiempo_min = str(row.get("Tiempo_Min", "-"))
            eval_tiempo = str(row.get("Evaluacion_Tiempo", "N/A"))

            valores = (num, agrupacion, geocerca, tipo, hora_in_str, hora_out_str, sentido, estado, tiempo_min, eval_tiempo)
            self.tree.insert("", "end", values=valores)