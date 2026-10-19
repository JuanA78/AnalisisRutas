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

            # Leer las primeras filas sin header para inspeccionar encabezados combinados
            df_raw = pd.read_excel(excel_file, sheet_name=sheet_target, header=None)

            # 1. Encontrar la fila de datos inicial (donde aparece 'AGRUPA' o 'GROUPING')
            header_idx = 0
            for i in range(min(15, len(df_raw))):
                fila_str = df_raw.iloc[i].astype(str).str.upper().tolist()
                if any("AGRUPA" in v or "GROUPING" in v or "UNIDAD" in v for v in fila_str):
                    header_idx = i
                    break

            # Releer con la fila de encabezados identificada
            self.df = pd.read_excel(excel_file, sheet_name=sheet_target, header=header_idx)

            # Detectar todas las columnas que hablen de Kilometraje
            cols_km = []
            for col in self.df.columns:
                c_upper = str(col).strip().upper()
                # Si el encabezado menciona 'TODOS' o 'MENSAJES'
                if "TODOS" in c_upper or "MENSAJE" in c_upper:
                    cols_km.append((col, 100)) # Prioridad máxima
                elif "KILOMETRAJE" in c_upper or "KM" in c_upper or "UNNAMED" in c_upper:
                    cols_km.append((col, 1))

            col_km_deseada = None
            
            # Si hay coincidencia por texto de alta prioridad
            coincidencias_top = [c for c, prio in cols_km if prio == 100]
            if coincidencias_top:
                col_km_deseada = coincidencias_top[0]
            elif len(cols_km) >= 2:
                # La ÚLTIMA columna de kilometraje en el Excel es SIEMPRE "en todos los mensajes"
                col_km_deseada = cols_km[-1][0]
            elif len(self.df.columns) >= 3:
                # Si no detectó los nombres por celdas combinadas, la columna 3 (índice 2) en base 0
                # en el reporte de Wialon es "Kilometraje en todos los mensajes"
                col_km_deseada = self.df.columns[2]

            # Si se encontró la columna objetivo, la renombramos
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