import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd

from visualizaciones.grafico_circular_estadisticos import GraficoPaiUnidades
from configuracion.colores import PaletaColores

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_DISPONIBLE = True
except ImportError:
    REPORTLAB_DISPONIBLE = False


class VistaGraficaCircularEstadisticos(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent)
        self.df_resultado = pd.DataFrame()
        self.configure(style="Main.TFrame")

        self._crear_encabezado_acciones()

        self.grafica_pastel = GraficoPaiUnidades(self)
        self.grafica_pastel.pack(fill="both", expand=True)

    def _crear_encabezado_acciones(self):
        frame_top = tk.Frame(self, bg=getattr(PaletaColores, "PANEL_LATERAL", "#1E293B"), padx=12, pady=8)
        frame_top.pack(fill="x")

        tk.Label(
            frame_top,
            text="Estadísticas de Cumplimiento por Unidad",
            bg=getattr(PaletaColores, "PANEL_LATERAL", "#1E293B"),
            fg=getattr(PaletaColores, "CELESTE_VIBRANTE", "#38BDF8"),
            font=("Segoe UI", 11, "bold")
        ).pack(side="left")

        btn_pdf = tk.Button(
            frame_top,
            text="📄 Exportar a PDF",
            command=self.exportar_a_pdf,
            bg="#0284C7",
            fg="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            cursor="hand2"
        )
        btn_pdf.pack(side="right")

    def cargar_datos(self, df_resultado: pd.DataFrame):
        self.df_resultado = df_resultado.copy() if df_resultado is not None else pd.DataFrame()
        self.grafica_pastel.renderizar_pie_charts(self.df_resultado)

    def exportar_a_pdf(self):
        """Genera un documento PDF formal con el resumen estadístico por unidad."""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showerror("Librería Faltante", "Instala ReportLab para exportar a PDF:\npip install reportlab")
            return

        if self.df_resultado.empty:
            messagebox.showwarning("Atención", "No hay datos disponibles para exportar.")
            return

        archivo_dest = filedialog.asksaveasfilename(
            title="Guardar Reporte Estadístico",
            defaultextension=".pdf",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not archivo_dest:
            return

        try:
            doc = SimpleDocTemplate(
                archivo_dest,
                pagesize=letter,
                rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
            )
            styles = getSampleStyleSheet()

            titulo_style = ParagraphStyle(
                "Titulo",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=16,
                textColor=colors.HexColor("#0F172A"),
                spaceAfter=12
            )

            elementos = [
                Paragraph("REPORTE ESTADÍSTICO DE CUMPLIMIENTO DE RUTAS", titulo_style),
                Spacer(1, 10)
            ]

            col_unidad = next((c for c in self.df_resultado.columns if "AGRUPA" in c.upper() or "UNIDAD" in c.upper()), "Agrupación")
            unidades = sorted(self.df_resultado[col_unidad].astype(str).unique().tolist())

            tabla_datos = [["Unidad", "A Tiempo", "Retrasos", "Adelantos", "Omisiones", "Cortes Ruta", "Retraso Total"]]

            for u in unidades:
                df_u = self.df_resultado[self.df_resultado[col_unidad].astype(str) == u]
                
                a_tiempo, retrasos, adelantos, omisiones, cortes = 0, 0, 0, 0, 0
                segs_ret = 0.0

                for _, r in df_u.iterrows():
                    eval_t = str(r.get("Evaluacion_Tiempo", ""))
                    estado = str(r.get("Estado_Ruta", ""))
                    tipo = str(r.get("Tipo", ""))
                    geo = str(r.get("Geocerca", ""))
                    s_r = r.get("Segundos_Retraso", 0.0)

                    if isinstance(s_r, (int, float)) and s_r > 0:
                        segs_ret += s_r

                    if "NO REGISTRADA" in estado or "Omitida" in tipo or "Faltante" in geo:
                        omisiones += 1
                    elif "CORTE" in estado or "Corte" in tipo:
                        cortes += 1
                    elif "Retraso" in eval_t:
                        retrasos += 1
                    elif "Adelanto" in eval_t:
                        adelantos += 1
                    elif "A Tiempo" in eval_t:
                        a_tiempo += 1

                mins_tot = f"+{round(segs_ret / 60.0, 1)}m" if segs_ret > 0 else "0m"
                tabla_datos.append([u, str(a_tiempo), str(retrasos), str(adelantos), str(omisiones), str(cortes), mins_tot])

            t = Table(tabla_datos, colWidths=[80, 70, 70, 70, 70, 70, 80])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#38BDF8")),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]))

            elementos.append(t)
            doc.build(elementos)
            messagebox.showinfo("Éxito", f"Reporte exportado correctamente:\n{os.path.basename(archivo_dest)}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")