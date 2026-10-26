import pandas as pd
from configuracion.rutas_config import RutasConfig


class LectorActividadGPS:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df = None

    def _obtener_unidades_permitidas(self, ruta_seleccionada: str = None) -> set:
        """
        [Mantenido por retrocompatibilidad de API] 
        Retorna conjunto vacío si se requiere omitir restricciones.
        """
        return set()

    def cargar_datos_completos(self, ruta_seleccionada: str = None) -> pd.DataFrame:
        """
        Lee y procesa TODAS las unidades presentes en el reporte de Wialon
        sin aplicar filtros por catálogo de ruta.
        
        Index 0: Agrupación / Grouping
        Index 1: Kilometraje en viajes
        Index 2: Kilometraje (en todos los mensajes)
        Index 3: Velocidad media
        Index 4: Velocidad Máxima
        Index 5: Tiempo en viajes
        Index 6: Horas de motor
        Index 7: Estacionamientos
        """
        try:
            if not self.filepath:
                return pd.DataFrame()

            excel_file = pd.ExcelFile(self.filepath)
            sheet_target = "Resumen" if "Resumen" in excel_file.sheet_names else 0

            # 1. Localizar dinámicamente el índice de la cabecera
            df_raw_check = pd.read_excel(excel_file, sheet_name=sheet_target, header=None)
            header_idx = 0
            for i in range(min(15, len(df_raw_check))):
                fila_str = df_raw_check.iloc[i].astype(str).str.upper().tolist()
                if any("GROUPING" in v or "AGRUPA" in v or "UNIDAD" in v for v in fila_str):
                    header_idx = i
                    break

            df_raw = pd.read_excel(excel_file, sheet_name=sheet_target, header=header_idx)

            if df_raw.empty or len(df_raw.columns) < 3:
                return pd.DataFrame()

            df_procesado = df_raw.copy()

            # 2. Mapeo estricto por posición ordinal de columnas
            posiciones = [
                "Agrupación",
                "Kilometraje en viajes",
                "Kilometraje",
                "Velocidad media",
                "Velocidad Máxima",
                "Tiempo en viajes",
                "Horas de motor",
                "Estacionamientos"
            ]
            
            col_map = {
                df_raw.columns[i]: posiciones[i] 
                for i in range(min(len(df_raw.columns), len(posiciones)))
            }

            df_procesado.rename(columns=col_map, inplace=True)

            # Limpieza básica del ID de unidad y filtrado de nulos/basura de totales
            df_procesado["Agrupación"] = df_procesado["Agrupación"].astype(str).str.strip()
            df_procesado = df_procesado[
                df_procesado["Agrupación"].notna() & 
                ~df_procesado["Agrupación"].str.lower().isin(["nan", "none", "", "total", "-----"])
            ].copy()

            # 3. Formateadores optimizados
            def formatear_km(val):
                if pd.isna(val) or str(val).strip() in ["nan", "None", ""]:
                    return "0.00 km"
                val_limpio = str(val).replace("km", "").strip()
                try:
                    return f"{float(val_limpio):.2f} km"
                except ValueError:
                    return str(val)

            def formatear_velocidad(val):
                if pd.isna(val) or str(val).strip() in ["nan", "None", ""]:
                    return "0 km/h"
                val_limpio = str(val).replace("km/h", "").strip()
                try:
                    return f"{round(float(val_limpio))} km/h"
                except ValueError:
                    return str(val)

            for col_km in ["Kilometraje en viajes", "Kilometraje"]:
                if col_km in df_procesado.columns:
                    df_procesado[col_km] = df_procesado[col_km].apply(formatear_km)

            if "Velocidad media" in df_procesado.columns:
                df_procesado["Velocidad media"] = df_procesado["Velocidad media"].apply(formatear_velocidad)

            # 4. Retorno directo SIN filtro de lista blanca
            self.df = df_procesado.reset_index(drop=True)
            return self.df

        except Exception as e:
            raise RuntimeError(f"Error al cargar datos completos de Actividad Diaria: {e}")

    def cargar_resumen_general(self, ruta_seleccionada: str = None) -> pd.DataFrame:
        """Vista simplificada de métricas clave sin restricción de ruta."""
        try:
            df_completo = self.cargar_datos_completos(ruta_seleccionada)
            if df_completo.empty:
                return pd.DataFrame()

            cols_deseadas = [
                col for col in ["Agrupación", "Kilometraje", "Velocidad Máxima", "Tiempo en viajes"]
                if col in df_completo.columns
            ]

            return df_completo[cols_deseadas].copy()

        except Exception as e:
            raise RuntimeError(f"Error al cargar resumen general: {e}")