# -*- coding: utf-8 -*-
"""
Personal Library Tracker — Application Factory
=================================================
Configura la instancia de Flask y registra el Blueprint de rutas.
"""

import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.config import Config, BASE_DIR

csrf = CSRFProtect()

def create_app():
    """
    Factory function que crea y configura la instancia de Flask.

    Returns:
        Flask: Aplicación Flask configurada y lista para ejecutarse.
    """
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, "app", "static"),
        template_folder=os.path.join(BASE_DIR, "app", "templates"),
    )

    # --- Configuración ---
    app.config.from_object(Config)
    
    # --- Seguridad ---
    csrf.init_app(app)

    # --- Base de Datos ---
    from app.models import close_connection
    app.teardown_appcontext(close_connection)

    # --- Registrar Rutas (Blueprint) ---
    from app.routes import main
    app.register_blueprint(main)

    return app
