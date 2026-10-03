import pandas as pd

class RutaService:
    # Definición de tramos de geocercas
    SECUENCIA_IDA = ["La Cruz", "Polo Norte", "Iberia", "CTM"]
    SECUENCIA_REGRESO = ["CTM", "Iberia", "Polo Norte", "La Cruz"]

    # Tiempos objetivo en minutos entre geocercas (aplica igual para ida y regreso)
    TIEMPOS_OBJETIVO = {
        ("La Cruz", "Polo Norte"): 25,
        ("Polo Norte", "La Cruz"): 25,
        ("Polo Norte", "Iberia"): 5,
        ("Iberia", "Polo Norte"): 5,
        ("Iberia", "CTM"): 13,
        ("CTM", "Iberia"): 13
    }

    @classmethod
    def analizar_unidad(cls, df_unidad: pd.DataFrame):
        resultados = []
        if df_unidad.empty:
            return pd.DataFrame(resultados)

        # Detectar el punto de inicio de la unidad
        primer_registro_geocerca = ""
        for _, row in df_unidad.iterrows():
            g_nombre = str(row.get('Geocerca', '')).strip()
            if g_nombre in ["La Cruz", "CTM"]:
                primer_registro_geocerca = g_nombre
                break

        if primer_registro_geocerca == "CTM":
            sentido_actual = "Regreso"
            secuencia_actual = cls.SECUENCIA_REGRESO
        else:
            sentido_actual = "Ida"
            secuencia_actual = cls.SECUENCIA_IDA

        paso_index = 0
        total_pasos = len(secuencia_actual)
        
        # Variables para rastrear el recorrido del tramo
        salida_anterior = None
        geocerca_anterior = None

        for _, row in df_unidad.iterrows():
            val_geocerca = row.get('Geocerca', '')
            if pd.isna(val_geocerca):
                continue
            
            geocerca_actual = str(val_geocerca).strip()
            if not geocerca_actual:
                continue

            # Obtener Hora de salida actual
            hora_salida_actual = pd.to_datetime(row.get('Hora de salida'), dayfirst=True, errors='coerce')

            geocerca_esperada = secuencia_actual[paso_index]
            
            # Variables de tiempo por defecto
            tiempo_transcurrido_str = "-"
            evaluacion_tiempo = "N/A"

            if geocerca_actual == geocerca_esperada:
                estado = f"Correcto ({paso_index + 1}/{total_pasos})"
                
                # Cálculo de tiempo desde la salida anterior hasta la salida actual
                if salida_anterior is not None and pd.notna(hora_salida_actual) and geocerca_anterior is not None and paso_index > 0:
                    diferencia_segundos = (hora_salida_actual - salida_anterior).total_seconds()
                    
                    minutos = int(diferencia_segundos // 60)
                    segundos = int(diferencia_segundos % 60)
                    tiempo_transcurrido_str = f"{minutos}m {segundos}s"
                    
                    # Tiempo objetivo
                    par_geocercas = (geocerca_anterior, geocerca_actual)
                    tiempo_objetivo_min = cls.TIEMPOS_OBJETIVO.get(par_geocercas)

                    if tiempo_objetivo_min is not None:
                        segundos_objetivo = tiempo_objetivo_min * 60
                        dif_seg = diferencia_segundos - segundos_objetivo
                        
                        if dif_seg > 0:
                            m_exc, s_exc = int(dif_seg // 60), int(dif_seg % 60)
                            evaluacion_tiempo = f"Exceso (+{m_exc}m {s_exc}s)"
                        elif dif_seg < 0:
                            dif_abs = abs(dif_seg)
                            m_men, s_men = int(dif_abs // 60), int(dif_abs % 60)
                            evaluacion_tiempo = f"Adelantado (-{m_men}m {s_men}s)"
                        else:
                            evaluacion_tiempo = "Tiempo Exacto"

                # Actualizar referencias para la siguiente fila
                salida_anterior = hora_salida_actual
                geocerca_anterior = geocerca_actual

                paso_index += 1

                # Si completó el tramo, alternar sentido
                if paso_index >= total_pasos:
                    if sentido_actual == "Ida":
                        sentido_actual = "Regreso"
                        secuencia_actual = cls.SECUENCIA_REGRESO
                    else:
                        sentido_actual = "Ida"
                        secuencia_actual = cls.SECUENCIA_IDA
                    paso_index = 1
            else:
                # Repetición o desviación
                paso_previo = max(0, paso_index - 1)
                if geocerca_actual == secuencia_actual[paso_previo]:
                    estado = "Repetición de Geocerca"
                else:
                    if geocerca_actual == "La Cruz":
                        sentido_actual = "Ida"
                        secuencia_actual = cls.SECUENCIA_IDA
                        paso_index = 1
                        estado = "Inicio/Reinicio en La Cruz (Ida)"
                    elif geocerca_actual == "CTM":
                        sentido_actual = "Regreso"
                        secuencia_actual = cls.SECUENCIA_REGRESO
                        paso_index = 1
                        estado = "Inicio/Reinicio en CTM (Regreso)"
                    else:
                        estado = f"Desviación (Esperaba: {geocerca_esperada})"

                # En caso de reinicio/desviación, actualizamos los puntos de origen
                salida_anterior = hora_salida_actual
                geocerca_anterior = geocerca_actual

            registro = row.to_dict()
            registro['Sentido'] = sentido_actual
            registro['Estado_Ruta'] = estado
            registro['Tiempo_Min'] = tiempo_transcurrido_str
            registro['Evaluacion_Tiempo'] = evaluacion_tiempo
            resultados.append(registro)

        return pd.DataFrame(resultados)