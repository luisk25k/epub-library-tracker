# -*- coding: utf-8 -*-
"""
Personal Library Tracker — Punto de Entrada
=============================================
Ejecuta la aplicación Flask en modo desarrollo.
Uso: python run.py
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Personal Library Tracker")
    print("  http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
