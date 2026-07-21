# -*- coding: utf-8 -*-
"""
Personal Library Tracker — Book Service
=========================================
Capa de servicio que orquesta las operaciones de negocio sobre libros.
Actúa como intermediario entre las rutas (routes.py) y la capa de datos
(models.py) + el parser ePub (epub_parser.py).

Responsabilidades:
- Coordinar la ingesta de ePub (parsing + creación en BD).
- Manejar la lógica de eliminación de portadas al borrar un libro.
- Validar datos de entrada antes de pasarlos a la capa de datos.
"""

import os
import uuid
import tempfile
import urllib.request
from werkzeug.utils import secure_filename
from app.models import create_book, get_book_by_id, update_book, delete_book
from app.services.epub_parser import parse_epub, delete_cover_file


# =============================================================================
# Constantes
# =============================================================================

# Tamaño máximo de archivo ePub (50 MB según requerimientos)
MAX_EPUB_SIZE = 50 * 1024 * 1024  # 50 MB en bytes

# Campos válidos para la creación/actualización de libros
VALID_BOOK_FIELDS = {
    "title", "author", "publisher", "translator", "language",
    "isbn", "year_published", "num_pages", "format",
    "reading_status", "rating", "cover_path", "review"
}

# Valores válidos para reading_status
VALID_STATUSES = {"No leído", "Leyendo", "Leído"}

# Valores válidos para format
VALID_FORMATS = {"digital", "physical"}


# =============================================================================
# Helper de Archivos
# =============================================================================

def save_uploaded_cover(file_storage) -> str:
    """
    Guarda una imagen de portada subida manualmente por el usuario.
    Retorna la ruta relativa para almacenar en BD.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    COVERS_DIR = os.path.join(BASE_DIR, "static", "uploads", "covers")
    os.makedirs(COVERS_DIR, exist_ok=True)
    
    ext = os.path.splitext(file_storage.filename)[1]
    if not ext:
        ext = ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(COVERS_DIR, unique_name)
    file_storage.save(save_path)
    return f"uploads/covers/{unique_name}"


def download_external_cover(url: str) -> str:
    """
    Descarga una imagen de portada desde una URL externa (ej. Google Books)
    y la guarda localmente para preservar la privacidad 100% local.
    """
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    COVERS_DIR = os.path.join(BASE_DIR, "static", "uploads", "covers")
    os.makedirs(COVERS_DIR, exist_ok=True)
    
    unique_name = f"{uuid.uuid4().hex}.jpg"
    save_path = os.path.join(COVERS_DIR, unique_name)
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
        out_file.write(response.read())
        
    return f"uploads/covers/{unique_name}"


# =============================================================================
# Funciones de Servicio
# =============================================================================

def ingest_epub(file_storage) -> dict:
    """
    Procesa un archivo ePub subido: guarda temporalmente el archivo,
    extrae metadatos y portada, y crea el registro en la BD.

    Args:
        file_storage: Objeto FileStorage de Flask (request.files['epub']).

    Returns:
        dict: Resultado con el ID del libro creado y los metadatos extraídos.

    Raises:
        ValueError: Si el archivo no es un .epub o excede el tamaño máximo.
    """
    # Validar extensión del archivo
    filename = file_storage.filename or ""
    if not filename.lower().endswith(".epub"):
        raise ValueError("El archivo debe tener extensión .epub")

    # Guardar temporalmente el archivo para procesarlo
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, filename)

    try:
        file_storage.save(temp_path)

        # Validar tamaño del archivo
        file_size = os.path.getsize(temp_path)
        if file_size > MAX_EPUB_SIZE:
            raise ValueError(f"El archivo excede el límite de {MAX_EPUB_SIZE // (1024*1024)} MB")

        # Extraer metadatos del ePub
        metadata = parse_epub(temp_path)

        # Crear el registro en la base de datos
        book_id = create_book(metadata)

        return {
            "id": book_id,
            "metadata": metadata,
            "message": f"Libro '{metadata['title']}' importado exitosamente"
        }

    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


def create_book_manual(data: dict, cover_file=None) -> dict:
    """
    Crea un libro manualmente a partir de datos del formulario.

    Args:
        data: Diccionario con los campos del libro.
        cover_file: Archivo de portada opcional.

    Returns:
        dict: Resultado con el ID del libro creado.

    Raises:
        ValueError: Si faltan campos obligatorios o hay datos inválidos.
    """
    # Validar campos obligatorios
    if not data.get("title", "").strip():
        raise ValueError("El título es obligatorio")
    if not data.get("author", "").strip():
        raise ValueError("El autor es obligatorio")

    # Validar reading_status si se proporciona
    if "reading_status" in data and data["reading_status"] not in VALID_STATUSES:
        raise ValueError(f"Estatus inválido. Opciones: {', '.join(VALID_STATUSES)}")

    # Validar format si se proporciona
    if "format" in data and data["format"] not in VALID_FORMATS:
        raise ValueError(f"Formato inválido. Opciones: {', '.join(VALID_FORMATS)}")

    # Filtrar solo campos válidos
    clean_data = {k: v for k, v in data.items() if k in VALID_BOOK_FIELDS and str(v).strip()}

    # Guardar portada si se subió una o si hay URL externa
    cover_url = data.get("cover_url")
    if cover_file and cover_file.filename:
        clean_data["cover_path"] = save_uploaded_cover(cover_file)
    elif cover_url:
        try:
            clean_data["cover_path"] = download_external_cover(cover_url)
        except Exception:
            pass # Ignorar fallos de descarga externa

    # Convertir year_published a entero si se proporciona
    if "year_published" in clean_data:
        try:
            clean_data["year_published"] = int(clean_data["year_published"])
        except (ValueError, TypeError):
            clean_data.pop("year_published", None)

    # Convertir num_pages a entero si se proporciona
    if "num_pages" in clean_data:
        try:
            clean_data["num_pages"] = int(clean_data["num_pages"])
        except (ValueError, TypeError):
            clean_data.pop("num_pages", None)
            
    # Convertir rating a entero si se proporciona
    if "rating" in clean_data:
        try:
            val = int(clean_data["rating"])
            if val < 0 or val > 5: raise ValueError
            clean_data["rating"] = val
        except (ValueError, TypeError):
            clean_data.pop("rating", None)

    book_id = create_book(clean_data)
    return {"id": book_id, "message": "Libro creado exitosamente"}


def update_book_data(book_id: int, data: dict, cover_file=None) -> dict:
    """
    Actualiza los datos de un libro existente.

    Args:
        book_id: ID del libro a actualizar.
        data:    Diccionario con los campos a modificar.
        cover_file: Archivo de portada opcional.

    Returns:
        dict: Resultado de la operación.

    Raises:
        ValueError: Si el libro no existe o hay datos inválidos.
    """
    # Verificar que el libro existe
    existing = get_book_by_id(book_id)
    if not existing:
        raise ValueError(f"Libro con ID {book_id} no encontrado")

    # Validar reading_status si se proporciona
    if "reading_status" in data and data["reading_status"] not in VALID_STATUSES:
        raise ValueError(f"Estatus inválido. Opciones: {', '.join(VALID_STATUSES)}")

    # Validar format si se proporciona
    if "format" in data and data["format"] not in VALID_FORMATS:
        raise ValueError(f"Formato inválido. Opciones: {', '.join(VALID_FORMATS)}")

    # Filtrar solo campos válidos
    clean_data = {k: v for k, v in data.items() if k in VALID_BOOK_FIELDS}
    
    # Procesar portada si se subió una o hay URL
    cover_url = data.get("cover_url")
    if cover_file and cover_file.filename:
        if existing.get("cover_path"):
            delete_cover_file(existing["cover_path"])
        clean_data["cover_path"] = save_uploaded_cover(cover_file)
    elif cover_url:
        try:
            if existing.get("cover_path"):
                delete_cover_file(existing["cover_path"])
            clean_data["cover_path"] = download_external_cover(cover_url)
        except Exception:
            pass

    # Convertir tipos numéricos
    if "year_published" in clean_data:
        try:
            val = clean_data["year_published"]
            clean_data["year_published"] = int(val) if str(val).strip() else None
        except (ValueError, TypeError):
            clean_data.pop("year_published", None)

    if "num_pages" in clean_data:
        try:
            val = clean_data["num_pages"]
            clean_data["num_pages"] = int(val) if str(val).strip() else None
        except (ValueError, TypeError):
            clean_data.pop("num_pages", None)
            
    if "rating" in clean_data:
        try:
            val = clean_data["rating"]
            if str(val).strip():
                int_val = int(val)
                if int_val < 0 or int_val > 5: raise ValueError
                clean_data["rating"] = int_val
            else:
                clean_data["rating"] = 0
        except (ValueError, TypeError):
            clean_data.pop("rating", None)

    success = update_book(book_id, clean_data)
    if success:
        return {"message": "Libro actualizado exitosamente"}
    else:
        raise ValueError("No se pudo actualizar el libro")


def remove_book(book_id: int) -> dict:
    """
    Elimina un libro de la BD y su imagen de portada asociada del disco.

    Args:
        book_id: ID del libro a eliminar.

    Returns:
        dict: Resultado de la operación.

    Raises:
        ValueError: Si el libro no existe.
    """
    deleted_book = delete_book(book_id)
    if not deleted_book:
        raise ValueError(f"Libro con ID {book_id} no encontrado")

    # Eliminar la imagen de portada del sistema de archivos
    if deleted_book.get("cover_path"):
        delete_cover_file(deleted_book["cover_path"])

    return {
        "message": f"Libro '{deleted_book['title']}' eliminado exitosamente",
        "deleted_id": book_id
    }


def search_isbn(isbn: str) -> dict:
    """Busca metadatos por ISBN intentando varias estrategias en orden de coste."""
    import json
    import re
    
    isbn = isbn.replace('-', '').strip()
    api_key = os.environ.get('GOOGLE_BOOKS_API_KEY')
    
    # ==========================================================
    # Intento 1: OpenLibrary (100% Libre y sin cuotas)
    # ==========================================================
    ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json"
    try:
        req = urllib.request.Request(ol_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            book_key = f"ISBN:{isbn}"
            if book_key in data:
                book = data[book_key]
                
                # Extraer año
                year = ""
                if book.get("publish_date"):
                    match = re.search(r'\d{4}', book["publish_date"])
                    if match: year = match.group(0)
                    
                cover_url = ""
                if book.get("cover"):
                    cover_url = book["cover"].get("large") or book["cover"].get("medium", "")

                return {
                    "title": book.get("title", ""),
                    "author": ", ".join([a.get("name", "") for a in book.get("authors", [])]),
                    "publisher": ", ".join([p.get("name", "") for p in book.get("publishers", [])]),
                    "year_published": year,
                    "num_pages": book.get("number_of_pages", ""),
                    "language": "", 
                    "cover_url": cover_url
                }
    except Exception:
        pass

    # Helper interno para procesar respuesta de Google Books
    def _fetch_google_books(query_url):
        req = urllib.request.Request(query_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get("totalItems", 0) > 0 and data.get("items"):
                vol = data["items"][0].get("volumeInfo", {})
                return {
                    "title": vol.get("title", ""),
                    "author": ", ".join(vol.get("authors", [])),
                    "publisher": vol.get("publisher", ""),
                    "year_published": vol.get("publishedDate", "")[:4] if vol.get("publishedDate") else "",
                    "num_pages": vol.get("pageCount", ""),
                    "language": vol.get("language", ""),
                    "cover_url": vol.get("imageLinks", {}).get("thumbnail", "").replace("http:", "https:")
                }
        return None

    # ==========================================================
    # Intento 2: Google Books API Pública (Sin API Key)
    # ==========================================================
    try:
        res = _fetch_google_books(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}")
        if res: return res
        res = _fetch_google_books(f"https://www.googleapis.com/books/v1/volumes?q={isbn}")
        if res: return res
    except Exception:
        # Falló silenciosamente (probablemente Error 429 Límite de Cuota)
        pass

    # ==========================================================
    # Intento 3: Google Books API Privada (Con API Key)
    # ==========================================================
    if api_key:
        try:
            res = _fetch_google_books(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={api_key}")
            if res: return res
            res = _fetch_google_books(f"https://www.googleapis.com/books/v1/volumes?q={isbn}&key={api_key}")
            if res: return res
        except Exception:
            pass
            
    return None
