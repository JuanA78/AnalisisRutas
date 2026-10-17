# lectores_excel/lector_actividad_gps.py 
import pandas as pd


class LectorActividadGPS:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df = None

    def cargar_datos(self) -> pd.DataFrame:
        try:
            if not self.filepath:
                return pd.DataFrame()

            excel_file = pd.ExcelFile(self.filepath)
            sheet_target = (
                "Resumen" if "Resumen" in excel_file.sheet_names else 0
            )

            df_temp = pd.read_excel(excel_file, sheet_name=sheet_target)

            # Buscar la fila de encabezados
            header_row = 0
            for i in range(min(15, len(df_temp))):
                row_vals = (
                    df_temp.iloc[i].astype(str).str.strip().str.upper().tolist()
                )
                if any("AGRUPA" in v or "KILOMETRAJE" in v for v in row_vals):
                    header_row = i + 1
                    break

            if header_row > 0:
                self.df = pd.read_excel(
                    excel_file, sheet_name=sheet_target, header=header_row
                )
            else:
                self.df = df_temp

            self.df.columns = self.df.columns.astype(str).str.strip()

            # -------------------------------------------------------------
            # BÚSQUEDA POR NOMBRE EXACTO O POR POSICIÓN (COLUMNA 2)
            # -------------------------------------------------------------
            col_km_deseada = None

            # 1. Intentar por coincidencia de nombre de columna
            for col in self.df.columns:
                col_u = col.upper()
                if "TODOS LOS MENSAJES" in col_u or "TODOS LOS MENSAJE" in col_u:
                    col_km_deseada = col
                    break

            # 2. Si no la encuentra por nombre, tomar directamente la Posición 2 (3ra Columna)
            if not col_km_deseada and len(self.df.columns) >= 3:
                col_km_deseada = self.df.columns[2]

            # Renombrar esa columna elegida a "Kilometraje"
            if col_km_deseada:
                self.df.rename(columns={col_km_deseada: "Kilometraje"}, inplace=True)

            if "Kilometraje" in self.df.columns:
                self.df["Kilometraje"] = self.df["Kilometraje"].apply(
                    lambda v: str(v).strip() if pd.notna(v) and str(v).strip() not in ["nan", "None", ""] else "0 km"
                )

            return self.df
        except Exception as e:
            raise RuntimeError(
                f"Error al cargar el archivo de Actividad Diaria: {e}"
            )