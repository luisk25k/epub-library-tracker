# -*- coding: utf-8 -*-
"""
Personal Library Tracker — Application Factory
=================================================
Configura la instancia de Flask, registra el Blueprint de rutas
e inicializa la base de datos al arranque.
"""

import os
from flask import Flask
from app.models import init_db


def create_app():
    """
    Factory function que crea y configura la instancia de Flask.

    Returns:
        Flask: Aplicación Flask configurada y lista para ejecutarse.
    """
    # Determinar la ruta base del proyecto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "app", "static"),
        template_folder=os.path.join(base_dir, "app", "templates"),
    )

    # --- Configuración ---
    app.config["SECRET_KEY"] = "personal-library-tracker-local-only"
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB límite de upload

    # --- Inicializar Base de Datos ---
    init_db()

    # --- Registrar Rutas (Blueprint) ---
    from app.routes import main
    app.register_blueprint(main)

    return app
