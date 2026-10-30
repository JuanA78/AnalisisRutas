#!/bin/bash
cd "$(dirname "$0")"

echo "=========================================="
echo " Iniciando AnalizadorRutas en macOS..."
echo "=========================================="

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual de Python..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
else
    source venv/bin/activate
fi

# Ejecutar la aplicación
python main.py