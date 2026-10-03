import pandas as pd

class ExcelService:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def cargar_datos(self):
        """Lee el Excel, encuentra la fila de encabezados y convierte fechas."""
        df_raw = pd.read_excel(self.file_path, header=None)

        # 1. Ubicar la fila de encabezados
        header_row_idx = None
        for i, row in df_raw.iterrows():
            row_values = row.astype(str).str.strip().tolist()
            if 'Geocerca' in row_values or 'Agrupación' in row_values:
                header_row_idx = i
                break

        if header_row_idx is None:
            header_row_idx = 0

        # Leer especificando la fila de encabezado detectada
        self.df = pd.read_excel(self.file_path, header=header_row_idx)
        
        # Limpiar nombres de columnas
        self.df.columns = self.df.columns.astype(str).str.strip()

        col_geocerca = 'Geocerca' if 'Geocerca' in self.df.columns else None
        col_agrupacion = 'Agrupación' if 'Agrupación' in self.df.columns else None

        # 2. Filtrar encabezados repetidos y EXCLUIR la fila de "Total"
        if col_geocerca:
            self.df = self.df[self.df[col_geocerca].notna()]
            val_geocerca_str = self.df[col_geocerca].astype(str).str.strip().str.lower()
            
            # Excluir la fila del encabezado repetido y la fila del Total
            self.df = self.df[~val_geocerca_str.isin(['geocerca', 'total'])]

        if col_agrupacion:
            val_agrupacion_str = self.df[col_agrupacion].astype(str).str.strip().str.lower()
            # Excluir si la agrupación dice "Total"
            self.df = self.df[~val_agrupacion_str.str.contains('total', na=False)]
            
            # Rellenar valores nulos temporales para evitar fallos
            self.df[col_agrupacion] = self.df[col_agrupacion].fillna('Sin Agrupación').astype(str).str.strip()

        # 3. Convertir columnas de tiempo a datetime
        if 'Hora de entrada' in self.df.columns:
            self.df['Hora de entrada'] = pd.to_datetime(self.df['Hora de entrada'], dayfirst=True, errors='coerce')
        
        if 'Hora de salida' in self.df.columns:
            self.df['Hora de salida'] = pd.to_datetime(self.df['Hora de salida'], dayfirst=True, errors='coerce')

        # 4. Ordenar cronológicamente manteniendo todas las filas válidas
        if 'Hora de entrada' in self.df.columns and col_agrupacion:
            self.df = self.df.sort_values(by=[col_agrupacion, 'Hora de entrada'], na_position='last')

        return self.df

    def obtener_unidades(self):
        if self.df is None:
            self.cargar_datos()
            
        if 'Agrupación' in self.df.columns:
            unidades = self.df['Agrupación'].dropna().astype(str).str.strip().unique().tolist()
            # Filtrar valores no deseados o vacíos
            return [u for u in unidades if u and u.lower() not in ['-----', 'nan', 'sin agrupación', 'total']]
        return []

    def obtener_datos_unidad(self, unidad: str):
        if self.df is None:
            self.cargar_datos()
            
        if 'Agrupación' in self.df.columns:
            unidad_limpia = str(unidad).strip().lower()
            mask = self.df['Agrupación'].astype(str).str.strip().str.lower() == unidad_limpia
            return self.df[mask].copy()
        return pd.DataFrame()