
# configuracion/rutas_config.py
class RutasConfig:
    # -------------------------------------------------------------------------
    # 1. SECUENCIAS GEOGRÁFICAS (IDA Y REGRESO)
    # -------------------------------------------------------------------------
    SECUENCIAS_EL_ARBOLITO = [
        ["La Cruz", "Centro", "Polo Norte", "Iberia", "CTM", "Gavilan"],
        ["Gavilan", "CTM", "Iberia", "Polo Norte", "Centro", "La Cruz"],
    ]

    SECUENCIAS_AGUA_SALADA = [
        ["Canal_CasaEloy", "Centro", "Polo Norte", "Iberia", "AguaSalada"],
        ["AguaSalada", "Iberia", "Polo Norte", "Centro", "Canal_CasaEloy"],
    ]

    # -------------------------------------------------------------------------
    # 2. PUNTOS DE CORTE 
    # -------------------------------------------------------------------------
    CORTE_AGUA_SALADA = ["CORTEIMSS"]
    CORTE_EL_ARBOLITO = ["CentraldeAutobuses"]
    # -------------------------------------------------------------------------
    # 3. PUNTOS DE INICIO PERMITIDOS
    # -------------------------------------------------------------------------
    PUNTOS_INICIO_AGUA_SALADA = ["Canal_CasaEloy", "AguaSalada"]
    PUNTOS_INICIO_EL_ARBOLITO = ["La Cruz", "Gavilan", "CTM"]
    # -------------------------------------------------------------------------
    # 4. EJES X OFICIALES PARA LAS GRÁFICAS DE RECORRIDO
    # -------------------------------------------------------------------------
    EJE_X_EL_ARBOLITO = ["La Cruz", "Centro", "Polo Norte", "Iberia", "CTM", "Gavilan"]
    EJE_X_AGUA_SALADA = ["Canal_CasaEloy", "Centro", "Polo Norte", "Iberia", "AguaSalada"]

    # -------------------------------------------------------------------------
    # 5. INVENTARIO DE UNIDADES
    # -------------------------------------------------------------------------
    UNIDADES_EL_ARBOLITO = [
        "F2", "903", "V2", "D3", "M2", "L2", "W2", "S2", "E3", "933", "921", "928"
    ]

    UNIDADES_AGUA_SALADA = [
        "901 - MDVR", "O2--", "N4--", "926-", "Y---", "C---", "915-3", "A2--","925-"
    ]

    # -------------------------------------------------------------------------
    # 6. CONFIGURACIÓN NOMINAL DE TIEMPOS POR TRAMO (MINUTOS)
    # -------------------------------------------------------------------------
    TIEMPOS_ARBOLITO_IDA = [
        ("La Cruz ➔ Centro", "17"),
        ("Centro ➔ Polo Norte", "8"),
        ("Polo Norte ➔ Iberia", "5"),
        ("Iberia ➔ CTM", "13"),
        ("CTM ➔ Gavilan", "10"),
    ]

    TIEMPOS_ARBOLITO_REGRESO = [
        ("Gavilan ➔ CTM", "10"),
        ("CTM ➔ Iberia", "3"),
        ("Iberia ➔ Polo Norte", "5"),
        ("Polo Norte ➔ Centro", "12"),
        ("Centro ➔ La Cruz", "19"),
    ]

    TIEMPOS_AGUA_SALADA_IDA = [
        ("Canal_CasaEloy ➔ Centro", "15"),
        ("Centro ➔ Polo Norte", "10"),
        ("Polo Norte ➔ Iberia", "8"),
        ("Iberia ➔ AguaSalada", "17"),
    ]

    TIEMPOS_AGUA_SALADA_REGRESO = [
        ("AguaSalada ➔ Iberia", "17"),
        ("Iberia ➔ Polo Norte", "8"),
        ("Polo Norte ➔ Centro", "10"),
        ("Centro ➔ Canal_CasaEloy", "15"),
    ]

    @classmethod
    def obtener_ruta_predeterminada(cls, unidad_id: str) -> str:
        u_clean = str(unidad_id).strip().upper()
        
        for base in cls.UNIDADES_EL_ARBOLITO:
            if base in u_clean:
                return "El Arbolito"
                
        for base in cls.UNIDADES_AGUA_SALADA:
            if base in u_clean:
                return "Agua Salada"
                
        return "Sin Asignar"

    #comentado 