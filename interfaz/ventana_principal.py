import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from servicios.excel_service import ExcelService
from servicios.ruta_service import RutaService
from interfaz.tabla_resultados import TablaResultados

class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analizador de Rutas")
        self.geometry("950x600")

        self.excel_service = None

        # Panel de controles superior
        frame_top = ttk.Frame(self, padding=10)
        frame_top.pack(fill="x")

        btn_cargar = ttk.Button(frame_top, text="Cargar Excel", command=self.cargar_excel)
        btn_cargar.pack(side="left", padx=5)

        ttk.Label(frame_top, text="Unidad:").pack(side="left", padx=5)
        self.combo_unidades = ttk.Combobox(frame_top, state="readonly")
        self.combo_unidades.pack(side="left", padx=5)

        btn_analizar = ttk.Button(frame_top, text="Analizar", command=self.ejecutar_analisis)
        btn_analizar.pack(side="left", padx=5)

        # Componente Tabla
        self.tabla = TablaResultados(self)
        self.tabla.pack(fill="both", expand=True, padx=10, pady=10)

    def cargar_excel(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos de Excel", "*.xlsx *.xls")])
        if file_path:
            self.excel_service = ExcelService(file_path)
            unidades = self.excel_service.obtener_unidades()
            
            if unidades:
                self.combo_unidades['values'] = unidades
                self.combo_unidades.current(0)
                messagebox.showinfo("Éxito", f"Se cargaron {len(unidades)} unidad(es).")
            else:
                messagebox.showwarning("Atención", "No se encontraron unidades en el archivo.")

    def ejecutar_analisis(self):
        unidad_seleccionada = self.combo_unidades.get()
        if not unidad_seleccionada or not self.excel_service:
            messagebox.showerror("Error", "Selecciona una unidad y asegúrate de cargar un archivo.")
            return

        df_unidad = self.excel_service.obtener_datos_unidad(unidad_seleccionada)
        df_resultado = RutaService.analizar_unidad(df_unidad)
        
        self.tabla.cargar_datos(df_resultado)