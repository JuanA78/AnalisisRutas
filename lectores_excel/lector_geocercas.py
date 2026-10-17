# lectores_excel/lector_geocercas.py
import re
import pandas as pd


class LectorGeocercas:

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.df_raw = self._cargar_excel()

    def _cargar_excel(self) -> pd.DataFrame:
        try:
            excel_file = pd.ExcelFile(self.filepath)
            hojas = excel_file.sheet_names

            hoja_objetivo = None
            nombres_buscados = [
                "GEOCERCAS",
                "DETALLE",
                "REGISTROS",
                "PUNTO A PUNTO",
                "DATOS",
            ]

            for h in hojas:
                if h.strip().upper() in nombres_buscados:
                    hoja_objetivo = h
                    break

            if not hoja_objetivo:
                for h in hojas:
                    df_prueba = pd.read_excel(excel_file, sheet_name=h, nrows=10)
                    cols_upper = [str(c).strip().upper() for c in df_prueba.columns]
                    if any("GEOCERCA" in c for c in cols_upper):
                        hoja_objetivo = h
                        break

            if not hoja_objetivo:
                hoja_objetivo = hojas[1] if len(hojas) > 1 else hojas[0]

            df_temp = pd.read_excel(excel_file, sheet_name=hoja_objetivo)

            header_row = 0
            for i in range(min(15, len(df_temp))):
                row_vals = (
                    df_temp.iloc[i].astype(str).str.strip().str.upper().tolist()
                )
                if any(
                    k in row_vals
                    for k in [
                        "AGRUPACIÓN",
                        "AGRUPACION",
                        "UNIDAD",
                        "VEHICULO",
                        "GEOCERCA",
                    ]
                ):
                    header_row = i + 1
                    break

            if header_row > 0:
                df = pd.read_excel(
                    excel_file, sheet_name=hoja_objetivo, header=header_row
                )
            else:
                df = df_temp

            df.columns = df.columns.astype(str).str.strip()

            for col in df.columns:
                if col.upper() in ["AGRUPACION", "UNIDAD", "VEHICULO", "GROUPING"]:
                    df.rename(columns={col: "Agrupación"}, inplace=True)
                    break

            for col in df.columns:
                if any(k in col.upper() for k in ["GEOCERCA", "PUNTO", "SITIO"]):
                    df.rename(columns={col: "Geocerca"}, inplace=True)
                    break

            if not df.empty:
                col_agrup = (
                    "Agrupación" if "Agrupación" in df.columns else df.columns[0]
                )
                ultima_val = str(df[col_agrup].iloc[-1]).strip().upper()
                if any(
                    k in ultima_val
                    for k in ["TOTAL", "TOTALES", "PROMEDIO", "-----"]
                ):
                    df = df.iloc[:-1].copy()

            return df
        except Exception as e:
            raise RuntimeError(f"Error al leer el archivo de Geocercas: {e}")

    def obtener_unidades(self) -> list:
        if self.df_raw is None or self.df_raw.empty:
            return []

        col_agrup = (
            "Agrupación" if "Agrupación" in self.df_raw.columns else self.df_raw.columns[0]
        )

        unidades = (
            self.df_raw[col_agrup]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )
        return sorted(
            [
                u
                for u in unidades
                if u and u.lower() not in ["nan", "none", "-", "total"]
            ]
        )

    def obtener_datos_unidades(self, lista_unidades: list) -> pd.DataFrame:
        if self.df_raw is None or self.df_raw.empty or not lista_unidades:
            return pd.DataFrame()

        col_agrup = (
            "Agrupación" if "Agrupación" in self.df_raw.columns else self.df_raw.columns[0]
        )

        # Crear conjunto de claves limpias para comparación rápida y exacta
        claves_sel = set(
            re.sub(r"[^A-Z0-9]", "", str(u).upper()) for u in lista_unidades if u
        )

        def coincide_unidad(val):
            clave_val = re.sub(r"[^A-Z0-9]", "", str(val).upper())
            # Se requiere coincidencia exacta para evitar que partes de cadenas coincidan erróneamente
            return clave_val in claves_sel if clave_val else False

        mask = self.df_raw[col_agrup].apply(coincide_unidad)
        df_filtrado = self.df_raw[mask].copy()

        # Elimina filas completamente duplicadas si existen en el Excel de origen
        return df_filtrado.drop_duplicates()