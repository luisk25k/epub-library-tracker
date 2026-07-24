import os

import sys

# Determinar la ruta base del proyecto de manera centralizada
if getattr(sys, 'frozen', False):
    # PyInstaller mode
    BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    # Source mode
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Usamos permanentemente el disco de backups para los datos
DATA_DIR = r"E:\05_Backups\Library-Tracker"
os.makedirs(DATA_DIR, exist_ok=True)

class Config:
    """Configuración global de la aplicación."""
    # Claves de Seguridad
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-key-for-local-use-only")
    
    # Límites
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB límite de upload
    
    # Rutas Absolutas (Para vistas estáticas, usamos BASE_DIR, pero para BDD/Portadas usamos DATA_DIR)
    DATABASE_DIR = os.path.join(DATA_DIR, "database")
    DATABASE_PATH = os.path.join(DATABASE_DIR, "library.db")
    # Para desarrollo, covers_dir estaba dentro de app/static. Para exe, debe estar en DATA_DIR
    if getattr(sys, 'frozen', False):
        COVERS_DIR = os.path.join(DATA_DIR, "covers")
    else:
        COVERS_DIR = os.path.join(BASE_DIR, "app", "static", "uploads", "covers")

    # Asegurar que los directorios existan para evitar errores 500
    os.makedirs(DATABASE_DIR, exist_ok=True)
    os.makedirs(COVERS_DIR, exist_ok=True)
