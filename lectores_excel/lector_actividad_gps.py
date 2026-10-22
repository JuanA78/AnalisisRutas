import pandas as pd
from configuracion.rutas_config import RutasConfig


class LectorActividadGPS:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df = None

    def _obtener_unidades_permitidas(self, ruta_seleccionada: str = None) -> set:
        if ruta_seleccionada == "El Arbolito":
            return set(g.strip().upper() for g in RutasConfig.UNIDADES_EL_ARBOLITO)
        elif ruta_seleccionada == "Agua Salada":
            return set(g.strip().upper() for g in RutasConfig.UNIDADES_AGUA_SALADA)
        else:
            return set(
                [g.strip().upper() for g in RutasConfig.UNIDADES_EL_ARBOLITO] +
                [g.strip().upper() for g in RutasConfig.UNIDADES_AGUA_SALADA]
            )

    def cargar_datos_completos(self, ruta_seleccionada: str = None) -> pd.DataFrame:
        """
        Lee por POSICIÓN FÍSICA de columnas en Wialon:
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

            # 1. Identificar la fila donde inicia la cabecera
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

            # 2. Mapeo estricto por POSICIÓN NUMÉRICA
            col_map = {}
            if len(df_raw.columns) > 0: col_map[df_raw.columns[0]] = "Agrupación"
            if len(df_raw.columns) > 1: col_map[df_raw.columns[1]] = "Kilometraje en viajes"
            if len(df_raw.columns) > 2: col_map[df_raw.columns[2]] = "Kilometraje"
            if len(df_raw.columns) > 3: col_map[df_raw.columns[3]] = "Velocidad media"
            if len(df_raw.columns) > 4: col_map[df_raw.columns[4]] = "Velocidad Máxima"
            if len(df_raw.columns) > 5: col_map[df_raw.columns[5]] = "Tiempo en viajes"
            if len(df_raw.columns) > 6: col_map[df_raw.columns[6]] = "Horas de motor"
            if len(df_raw.columns) > 7: col_map[df_raw.columns[7]] = "Estacionamientos"

            df_procesado.rename(columns=col_map, inplace=True)
            df_procesado["Agrupación"] = df_procesado["Agrupación"].astype(str).str.strip()

            # 3. Formateo exacto de decimales y cadenas numéricas (estilo Excel Wialon)
            def formatear_km(val):
                if pd.isna(val) or str(val).strip() in ["nan", "None", ""]:
                    return "0.00 km"
                val_limpio = str(val).replace("km", "").strip()
                try:
                    num = float(val_limpio)
                    return f"{num:.2f} km"
                except ValueError:
                    return str(val)

            def formatear_velocidad(val):
                if pd.isna(val) or str(val).strip() in ["nan", "None", ""]:
                    return "0 km/h"
                val_limpio = str(val).replace("km/h", "").strip()
                try:
                    num = float(val_limpio)
                    return f"{round(num)} km/h"
                except ValueError:
                    return str(val)

            for col_km in ["Kilometraje en viajes", "Kilometraje"]:
                if col_km in df_procesado.columns:
                    df_procesado[col_km] = df_procesado[col_km].apply(formatear_km)

            if "Velocidad media" in df_procesado.columns:
                df_procesado["Velocidad media"] = df_procesado["Velocidad media"].apply(formatear_velocidad)

            # 4. Filtrar por unidades pertenecientes a la ruta seleccionada
            unidades_permitidas = self._obtener_unidades_permitidas(ruta_seleccionada)
            df_filtrado = df_procesado[
                df_procesado["Agrupación"].str.upper().isin(unidades_permitidas)
            ].copy()

            self.df = df_filtrado.reset_index(drop=True)
            return self.df

        except Exception as e:
            raise RuntimeError(f"Error al cargar datos completos de Actividad Diaria: {e}")

    def cargar_resumen_general(self, ruta_seleccionada: str = None) -> pd.DataFrame:
        """Vista simplificada de 3 métricas clave + Unidad."""
        try:
            df_completo = self.cargar_datos_completos(ruta_seleccionada)
            if df_completo.empty:
                return pd.DataFrame()

            cols_deseadas = ["Agrupación", "Kilometraje"]
            if "Velocidad Máxima" in df_completo.columns:
                cols_deseadas.append("Velocidad Máxima")
            if "Tiempo en viajes" in df_completo.columns:
                cols_deseadas.append("Tiempo en viajes")

            return df_completo[cols_deseadas].copy()

        except Exception as e:
            raise RuntimeError(f"Error al cargar resumen general: {e}")