import tkinter as tk
from tkinter import ttk


class Dashboard:

    def __init__(self, parent):

        self.parent = parent

        self.frame = ttk.Frame(
            parent
        )

        self.frame.pack(
            fill="x",
            padx=20,
            pady=(15, 10)
        )

        self.crear_tarjetas()


    def crear_tarjetas(self):

        self.tarjetas = {}

        configuracion = [
            (
                "unidades",
                "UNIDADES",
                "0"
            ),
            (
                "tramos",
                "TRAMOS ANALIZADOS",
                "0"
            ),
            (
                "rapidos",
                "MÁS RÁPIDOS",
                "0"
            ),
            (
                "lentos",
                "MÁS LENTOS",
                "0"
            ),
            (
                "promedio",
                "TIEMPO PROMEDIO",
                "0 min"
            )
        ]

        for columna, (clave, titulo, valor) in enumerate(
            configuracion
        ):

            tarjeta = ttk.Frame(
                self.frame,
                relief="solid",
                borderwidth=1
            )

            tarjeta.grid(
                row=0,
                column=columna,
                padx=5,
                sticky="nsew"
            )

            self.frame.columnconfigure(
                columna,
                weight=1
            )

            titulo_label = ttk.Label(
                tarjeta,
                text=titulo,
                font=(
                    "Segoe UI",
                    9,
                    "bold"
                )
            )

            titulo_label.pack(
                pady=(12, 2)
            )

            valor_label = ttk.Label(
                tarjeta,
                text=valor,
                font=(
                    "Segoe UI",
                    20,
                    "bold"
                )
            )

            valor_label.pack(
                pady=(2, 12)
            )

            self.tarjetas[clave] = valor_label


    def actualizar(
        self,
        unidades,
        tramos,
        rapidos,
        lentos,
        promedio
    ):

        self.tarjetas["unidades"].config(
            text=str(unidades)
        )

        self.tarjetas["tramos"].config(
            text=str(tramos)
        )

        self.tarjetas["rapidos"].config(
            text=str(rapidos)
        )

        self.tarjetas["lentos"].config(
            text=str(lentos)
        )

        self.tarjetas["promedio"].config(
            text=f"{promedio:.1f} min"
        )


    def limpiar(self):

        self.actualizar(
            0,
            0,
            0,
            0,
            0
        )