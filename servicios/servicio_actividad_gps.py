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
        Extrae las 3 métricas de Actividad GPS para el Resumen General.
        Prioriza la columna 'Kilometraje' ya filtrada por LectorActividadGPS.
        """
        if df_actividad is None or df_actividad.empty:
            return {}

        df = df_actividad.copy()

        # 1. Búsqueda de columna de unidad
        col_unidad = next((c for c in df.columns if any(k in str(c).upper() for k in ["GROUPING", "AGRUPA", "UNIDAD"])), None)

        # 2. Búsqueda de columna de Kilometraje (Prioriza 'Kilometraje' renombrada o 'TODOS LOS MENSAJES')
        col_km = None
        for c in df.columns:
            c_u = str(c).upper()
            if c_u == "KILOMETRAJE" or "TODOS LOS MENSAJES" in c_u or "KILOMETRAJE EN TODOS" in c_u:
                col_km = c
                break
        
        if not col_km:
            col_km = next((c for c in df.columns if "KILOMETRAJE" in str(c).upper() or "KM" in str(c).upper()), None)

        # 3. Búsqueda de Velocidad y Tiempo
        col_vel_max = next((c for c in df.columns if "VELOCIDAD MÁXIMA" in str(c).upper() or "VELOCIDAD MAXIMA" in str(c).upper() or "VELOCIDAD MÁX" in str(c).upper()), None)
        col_tiempo_viajes = next((c for c in df.columns if "TIEMPO EN VIAJES" in str(c).upper() or "TIEMPO VIAJES" in str(c).upper() or "TIEMPO DE VIAJES" in str(c).upper()), None)

        resultado = {}

        for _, fila in df.iterrows():
            u_raw = str(fila.get(col_unidad, "") if col_unidad else fila.iloc[0]).strip()
            u_norm = cls._normalizar_identificador(u_raw)

            if not u_norm or u_norm in ["NAN", "NONE", "GROUPING"]:
                continue

            # Extracción explícita
            km_val = fila.get(col_km, "-")
            vel_val = fila.get(col_vel_max, "-")
            tiempo_val = fila.get(col_tiempo_viajes, "-")

            # Formateo limpio de texto
            km_str = str(km_val).replace("km", "").strip() if pd.notna(km_val) else "-"
            vel_str = str(vel_val).replace("km/h", "").strip() if pd.notna(vel_val) else "-"

            resultado[u_norm] = {
                "km": f"{km_str} km" if km_str not in ["nan", "None", "", "-"] else "-",
                "velocidad_max": vel_str if vel_str not in ["nan", "None", ""] else "-",
                "tiempo_viajes": str(tiempo_val).strip() if pd.notna(tiempo_val) and str(tiempo_val).strip() not in ["nan", "None", ""] else "-"
            }

        return resultado