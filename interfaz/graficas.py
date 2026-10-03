import matplotlib.pyplot as plt


def mostrar_grafica(df):

    if df.empty:
        return


    datos = df.copy()

    datos["Tramo"] = (
        datos["Origen"]
        + " → "
        + datos["Destino"]
    )

    datos["Etiqueta"] = (
        datos["Unidad"]
        + "\n"
        + datos["Tramo"]
    )


    posiciones = range(
        len(datos)
    )


    fig, ax = plt.subplots(
        figsize=(14, 7)
    )


    ancho = 0.35


    tiempo_real = datos[
        "TiempoReal"
    ].tolist()

    tiempo_esperado = datos[
        "TiempoEsperado"
    ].tolist()


    posiciones_real = [
        posicion - ancho / 2
        for posicion in posiciones
    ]

    posiciones_esperado = [
        posicion + ancho / 2
        for posicion in posiciones
    ]


    barras_real = ax.bar(
        posiciones_real,
        tiempo_real,
        width=ancho,
        label="Tiempo real"
    )


    barras_esperado = ax.bar(
        posiciones_esperado,
        tiempo_esperado,
        width=ancho,
        label="Tiempo esperado"
    )


    ax.set_title(
        "Análisis de tiempos por unidad y tramo",
        fontsize=16,
        fontweight="bold"
    )


    ax.set_ylabel(
        "Tiempo (minutos)"
    )


    ax.set_xlabel(
        "Unidad / Tramo"
    )


    ax.set_xticks(
        list(posiciones)
    )


    ax.set_xticklabels(
        datos["Etiqueta"],
        rotation=45,
        ha="right"
    )


    ax.legend()


    ax.grid(
        axis="y",
        alpha=0.25
    )


    # Mostrar valor encima de cada barra

    for barra in barras_real:

        altura = barra.get_height()

        ax.text(
            barra.get_x()
            + barra.get_width() / 2,
            altura,
            f"{altura:.1f}",
            ha="center",
            va="bottom",
            fontsize=8
        )


    for barra in barras_esperado:

        altura = barra.get_height()

        ax.text(
            barra.get_x()
            + barra.get_width() / 2,
            altura,
            f"{altura:.1f}",
            ha="center",
            va="bottom",
            fontsize=8
        )


    plt.tight_layout()

    plt.show()