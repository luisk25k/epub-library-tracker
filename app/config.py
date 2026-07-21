import os

# Determinar la ruta base del proyecto de manera centralizada
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    """Configuración global de la aplicación."""
    # Claves de Seguridad
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-fallback-key-for-local-use-only")
    
    # Límites
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB límite de upload
    
    # Rutas Absolutas
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    DATABASE_PATH = os.path.join(DATABASE_DIR, "library.db")
    COVERS_DIR = os.path.join(BASE_DIR, "app", "static", "uploads", "covers")
