import os
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt

from visualizaciones.grafico_circular_estadisticos import GraficoPaiUnidades
from configuracion.colores import PaletaColores

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
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
            text="📄 Exportar Gráficas a PDF",
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

    def _generar_figura_maestra_unidades(self) -> plt.Figure:
        """Genera una figura unificada de Matplotlib con todas las unidades en retícula."""
        col_unidad = next((c for c in self.df_resultado.columns if "AGRUPA" in c.upper() or "UNIDAD" in c.upper()), None)
        if not col_unidad:
            return None

        unidades = sorted(self.df_resultado[col_unidad].astype(str).unique().tolist())
        if not unidades:
            return None

        COLUMNAS = 3
        filas = (len(unidades) + COLUMNAS - 1) // COLUMNAS

        # Crear figura global ajustando altura proporcional a la cantidad de filas
        fig, axes = plt.subplots(filas, COLUMNAS, figsize=(11, 3.5 * filas), dpi=150, facecolor="#FFFFFF")
        
        # Normalizar matriz de ejes
        if filas == 1 and COLUMNAS == 1:
            axes = [axes]
        elif filas == 1 or COLUMNAS == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()

        mapa_colores = {
            "A Tiempo": "#10B981",
            "Adelanto": "#F97316",
            "Retraso": "#EF4444",
            "Omisión": "#2563EB",
            "Corte Ruta": "#8B5CF6"
        }

        for i, unidad_id in enumerate(unidades):
            ax = axes[i]
            df_u = self.df_resultado[self.df_resultado[col_unidad].astype(str) == unidad_id]

            conteos = {
                "A Tiempo": 0, "Adelanto": 0, "Retraso": 0, "Omisión": 0, "Corte Ruta": 0
            }

            for _, r in df_u.iterrows():
                eval_t = str(r.get("Evaluacion_Tiempo", ""))
                estado = str(r.get("Estado_Ruta", ""))
                tipo = str(r.get("Tipo", ""))
                geo = str(r.get("Geocerca", ""))

                if "NO REGISTRADA" in estado or "Omitida" in tipo or "Faltante" in geo:
                    conteos["Omisión"] += 1
                elif "CORTE" in estado or "Corte" in tipo:
                    conteos["Corte Ruta"] += 1
                elif "Retraso" in eval_t:
                    conteos["Retraso"] += 1
                elif "Adelanto" in eval_t:
                    conteos["Adelanto"] += 1
                elif "A Tiempo" in eval_t:
                    conteos["A Tiempo"] += 1

            labels, sizes, colors_list = [], [], []
            total_eventos = sum(conteos.values())

            if total_eventos > 0:
                for cat, count in conteos.items():
                    if count > 0:
                        labels.append(cat)
                        sizes.append(count)
                        colors_list.append(mapa_colores[cat])

                ax.pie(
                    sizes,
                    labels=labels,
                    colors=colors_list,
                    autopct="%1.1f%%",
                    startangle=140,
                    textprops={"fontsize": 7, "fontweight": "bold", "color": "#1E293B"},
                    wedgeprops={"edgecolor": "#FFFFFF", "linewidth": 1.2}
                )

            ax.set_title(f"UNIDAD: {unidad_id}", color="#0F172A", fontsize=9, fontweight="bold", pad=6)

        # Ocultar ejes vacíos de la cuadrícula si los hay
        for j in range(len(unidades), len(axes)):
            axes[j].axis("off")

        plt.tight_layout()
        return fig

    def exportar_a_pdf(self):
        """Exporta las gráficas de pastel en un archivo PDF."""
        if not REPORTLAB_DISPONIBLE:
            messagebox.showerror("Librería Faltante", "Instala ReportLab para exportar a PDF:\npip install reportlab")
            return

        if self.df_resultado.empty:
            messagebox.showwarning("Atención", "No hay datos disponibles para exportar.")
            return

        archivo_dest = filedialog.asksaveasfilename(
            title="Guardar Reporte Gráfico en PDF",
            defaultextension=".pdf",
            filetypes=[("Documentos PDF", "*.pdf")]
        )

        if not archivo_dest:
            return

        ruta_img_temp = None
        figura_maestra = None
        try:
            # 1. Generar la figura unificada en memoria
            figura_maestra = self._generar_figura_maestra_unidades()

            if figura_maestra is None:
                messagebox.showerror("Error", "No se pudieron procesar las gráficas de las unidades.")
                return

            # 2. Guardar la figura maesra en un archivo temporal de alta resolución
            temp_dir = tempfile.gettempdir()
            ruta_img_temp = os.path.join(temp_dir, "grafica_maestra_pie_temp.png")

            figura_maestra.savefig(
                ruta_img_temp,
                dpi=180,
                bbox_inches="tight",
                facecolor="#FFFFFF",
                edgecolor="none"
            )
            plt.close(figura_maestra)

            # 3. Construir el documento con ReportLab
            doc = SimpleDocTemplate(
                archivo_dest,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            styles = getSampleStyleSheet()

            titulo_style = ParagraphStyle(
                "TituloReporte",
                parent=styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=14,
                textColor=colors.HexColor("#0F172A"),
                alignment=1,
                spaceAfter=12
            )

            elementos = [
                Paragraph("Graficas De Cumplimiento Por Unidad", titulo_style),
                Spacer(1, 10)
            ]

            # 4. Insertar imagen ajustada
            ancho_pag_util = 540
            alto_proporcional = min(680, int(ancho_pag_util * (figura_maestra.get_size_inches()[1] / figura_maestra.get_size_inches()[0])))

            img_pdf = Image(ruta_img_temp, width=ancho_pag_util, height=alto_proporcional)
            elementos.append(img_pdf)

            doc.build(elementos)

            messagebox.showinfo(
                "Éxito",
                f"Gráficas exportadas correctamente a PDF:\n{os.path.basename(archivo_dest)}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

        finally:
            if figura_maestra is not None:
                plt.close(figura_maestra)
            if ruta_img_temp and os.path.exists(ruta_img_temp):
                try:
                    os.remove(ruta_img_temp)
                except OSError:
                    pass