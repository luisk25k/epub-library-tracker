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
import tempfile
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
    "reading_status", "cover_path", "review"
}

# Valores válidos para reading_status
VALID_STATUSES = {"No leído", "Leyendo", "Leído"}

# Valores válidos para format
VALID_FORMATS = {"digital", "physical"}


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


def create_book_manual(data: dict) -> dict:
    """
    Crea un libro manualmente a partir de datos del formulario.

    Args:
        data: Diccionario con los campos del libro.

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
    clean_data = {k: v for k, v in data.items() if k in VALID_BOOK_FIELDS and v}

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

    book_id = create_book(clean_data)
    return {"id": book_id, "message": "Libro creado exitosamente"}


def update_book_data(book_id: int, data: dict) -> dict:
    """
    Actualiza los datos de un libro existente.

    Args:
        book_id: ID del libro a actualizar.
        data:    Diccionario con los campos a modificar.

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

    # Convertir tipos numéricos
    if "year_published" in clean_data:
        try:
            val = clean_data["year_published"]
            clean_data["year_published"] = int(val) if val else None
        except (ValueError, TypeError):
            clean_data.pop("year_published", None)

    if "num_pages" in clean_data:
        try:
            val = clean_data["num_pages"]
            clean_data["num_pages"] = int(val) if val else None
        except (ValueError, TypeError):
            clean_data.pop("num_pages", None)

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
