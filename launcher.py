import os
import sys
import threading
import time
import webbrowser
from app import create_app
from app.config import Config
from app.models import init_db

def open_browser():
    # Espera 1.5 segundos para asegurarse de que el servidor Flask esté levantado
    time.sleep(1.5)
    url = "http://127.0.0.1:5000/"
    webbrowser.open(url)

if __name__ == "__main__":
    # Inicia el hilo que abrirá el navegador
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Creamos la aplicación
    app = create_app()
    
    with app.app_context():
        init_db()
    
    # Arrancamos Flask en el hilo principal bloqueando la ejecución
    # use_reloader=False es crítico en PyInstaller para evitar procesos huérfanos
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
