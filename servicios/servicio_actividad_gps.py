import pandas as pd


class ServicioActividadGPS:
    """Lógica de negocio y filtrado para datos de Actividad Diaria GPS."""

    @staticmethod
    def _buscar_columna_unidad(df: pd.DataFrame):
        if df is None or df.empty:
            return None

        equivalencias = {
            "grouping",
            "agrupacion",
            "agrupación",
            "unidad",
            "vehicle",
            "vehiculo",
            "vehículo"
        }

        for columna in df.columns:
            nombre = str(columna).strip().casefold()
            if nombre in equivalencias:
                return columna

        return None

    @staticmethod
    def _normalizar_identificador(valor) -> str:
        if pd.isna(valor):
            return ""
        return str(valor).replace("-", "").strip().upper()

    @classmethod
    def _coincide_unidad(cls, valor_celda, seleccionadas: set) -> bool:
        unidad = cls._normalizar_identificador(valor_celda)
        if not unidad:
            return False

        if unidad in seleccionadas:
            return True

        for sel in seleccionadas:
            if unidad.startswith(f"{sel} ") or unidad.startswith(f"{sel}-") or sel in unidad:
                return True

        return False

    @classmethod
    def filtrar_actividad(
        cls,
        df_actividad: pd.DataFrame,
        unidades_sel: list = None
    ) -> pd.DataFrame:
        """
        Filtra el DataFrame de actividad GPS para mostrar solo las unidades seleccionadas.
        Si no hay selección, devuelve el DataFrame completo.
        """
        if df_actividad is None or df_actividad.empty:
            return pd.DataFrame()

        df = df_actividad.copy()
        columna_unidad = cls._buscar_columna_unidad(df)

        if columna_unidad is None or not unidades_sel:
            return df.reset_index(drop=True)

        seleccionadas = {
            cls._normalizar_identificador(u)
            for u in unidades_sel
        }
        seleccionadas.discard("")

        if not seleccionadas:
            return df.reset_index(drop=True)

        mascara = df[columna_unidad].apply(
            lambda val: cls._coincide_unidad(val, seleccionadas)
        )

        return df.loc[mascara].reset_index(drop=True)

    @classmethod
    def obtener_unidades(cls, df_actividad: pd.DataFrame) -> list:
        """Obtiene las unidades únicas detectadas en los datos GPS."""
        if df_actividad is None or df_actividad.empty:
            return []

        columna_unidad = cls._buscar_columna_unidad(df_actividad)
        if columna_unidad is None:
            return []

        unidades = (
            df_actividad[columna_unidad]
            .dropna()
            .astype(str)
            .str.strip()
        )
        unidades = unidades[unidades != ""]
        return sorted(unidades.unique().tolist())

    @classmethod
    def obtener_metricas_resumen(cls, df_actividad: pd.DataFrame) -> dict:
        """
        Extrae exclusivamente las 3 métricas de Actividad GPS para el Resumen General:
        - Km Mensajes (Kilometraje)
        - Velocidad Máxima
        - Tiempo Viajes
        Devuelve un diccionario estructurado por unidad { "UNIDAD_ID": {...} }
        """
        if df_actividad is None or df_actividad.empty:
            return {}

        df = df_actividad.copy()

        # Identificar columnas en el reporte GPS
        col_unidad = next(
            (c for c in df.columns if any(k in str(c).upper() for k in ["GROUPING", "AGRUPA", "UNIDAD", "VEHICU"])),
            None
        )
        col_km = next(
            (c for c in df.columns if any(k in str(c).upper() for k in ["KILOMETRAJE", "TODOS LOS MENSAJES", "KM"])),
            None
        )
        col_vel_max = next(
            (c for c in df.columns if "MÁXIMA" in str(c).upper() or "MAXIMA" in str(c).upper() or "VELOCIDAD" in str(c).upper()),
            None
        )
        col_tiempo_viajes = next(
            (c for c in df.columns if "TIEMPO EN VIAJES" in str(c).upper() or "TIEMPO VIAJES" in str(c).upper() or "DURACIÓN" in str(c).upper()),
            None
        )

        if not col_unidad:
            return {}

        resultado = {}
        for _, fila in df.iterrows():
            u_raw = str(fila.get(col_unidad, "")).strip()
            u_norm = cls._normalizar_identificador(u_raw)

            if not u_norm:
                continue

            km_val = fila.get(col_km, "-") if col_km else "-"
            vel_val = fila.get(col_vel_max, "-") if col_vel_max else "-"
            tiempo_val = fila.get(col_tiempo_viajes, "-") if col_tiempo_viajes else "-"

            resultado[u_norm] = {
                "km": str(km_val) if pd.notna(km_val) and str(km_val).strip() not in ["nan", "None", ""] else "-",
                "velocidad_max": str(vel_val) if pd.notna(vel_val) and str(vel_val).strip() not in ["nan", "None", ""] else "-",
                "tiempo_viajes": str(tiempo_val) if pd.notna(tiempo_val) and str(tiempo_val).strip() not in ["nan", "None", ""] else "-"
            }

        return resultado