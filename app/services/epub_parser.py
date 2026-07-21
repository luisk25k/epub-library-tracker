# -*- coding: utf-8 -*-
"""
Personal Library Tracker — ePub Parser Service
================================================
Módulo encargado de leer archivos .epub y extraer automáticamente:
- Metadatos Dublin Core: título, autor, editorial, idioma, ISBN.
- Imagen de portada: detecta la imagen declarada como cover en el manifiesto OPF.

Utiliza la librería 'ebooklib' para la lectura de la estructura ePub.

Referencia de metadatos ePub/Dublin Core:
- dc:title     → Título de la obra
- dc:creator   → Autor(es)
- dc:publisher → Editorial
- dc:language  → Idioma (ISO 639-1)
- dc:identifier → ISBN u otro identificador
"""

import os
import uuid
import ebooklib
from ebooklib import epub
from app.config import Config


# =============================================================================
# Extracción de Metadatos
# =============================================================================

def _get_metadata_value(book: epub.EpubBook, field: str) -> str:
    """
    Extrae un valor de metadato Dublin Core del libro ePub.

    Args:
        book:  Objeto EpubBook cargado.
        field: Nombre del campo DC (e.g. 'title', 'creator', 'publisher').

    Returns:
        str: Valor del metadato o None si no existe.
    """
    try:
        metadata = book.get_metadata("DC", field)
        if metadata and len(metadata) > 0:
            # metadata es una lista de tuplas: [(valor, atributos), ...]
            return metadata[0][0] if metadata[0][0] else None
    except Exception:
        pass
    return None


def _extract_isbn(book: epub.EpubBook) -> str:
    """
    Intenta extraer el ISBN del campo dc:identifier.
    Los ePub pueden tener múltiples identificadores; buscamos uno
    que contenga 'isbn' en sus atributos o en el valor mismo.

    Args:
        book: Objeto EpubBook cargado.

    Returns:
        str: ISBN encontrado o None.
    """
    try:
        identifiers = book.get_metadata("DC", "identifier")
        for value, attrs in identifiers:
            # Verificar si los atributos indican que es un ISBN
            attr_str = str(attrs).lower()
            if "isbn" in attr_str:
                return value
            # Verificar si el valor tiene formato ISBN
            # ISBN-10: 10 dígitos, ISBN-13: 13 dígitos (puede incluir guiones)
            cleaned = value.replace("-", "").replace(" ", "")
            if cleaned.isdigit() and len(cleaned) in (10, 13):
                return value
    except Exception:
        pass
    return None


# =============================================================================
# Extracción de Imagen de Portada
# =============================================================================

def _extract_cover_image(book: epub.EpubBook) -> str:
    """
    Busca la imagen de portada dentro del ePub utilizando 3 estrategias.

    Args:
        book:          Objeto EpubBook cargado.

    Returns:
        str: Ruta relativa de la imagen guardada (relativa a static/),
             o None si no se encontró portada.
    """
    cover_item = None

    # Estrategia 1: Buscar item con propiedad 'cover-image'
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_COVER:
            cover_item = item
            break

    # Estrategia 2: Buscar metadato 'cover' que apunte a un item del manifiesto
    if cover_item is None:
        try:
            cover_meta = book.get_metadata("OPF", "cover")
            if cover_meta:
                cover_id = cover_meta[0][1].get("content", "")
                if cover_id:
                    cover_item = book.get_item_with_id(cover_id)
        except (IndexError, KeyError, AttributeError):
            pass

    # Estrategia 3: Buscar el primer item de tipo imagen
    if cover_item is None:
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            # Priorizar imágenes con 'cover' en el nombre
            if "cover" in item.get_name().lower():
                cover_item = item
                break
        # Si aún no hay, tomar la primera imagen disponible
        if cover_item is None:
            images = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))
            if images:
                cover_item = images[0]

    # Si se encontró una imagen, guardarla en disco
    if cover_item is not None:
        return _save_cover_image(cover_item)

    return None


def _save_cover_image(item) -> str:
    """
    Guarda un item de imagen del ePub en el directorio de portadas.

    El nombre del archivo se genera con UUID para evitar colisiones.
    Se preserva la extensión original del archivo.

    Args:
        item: Item de imagen de ebooklib.

    Returns:
        str: Ruta relativa de la imagen guardada (para almacenar en BD).
    """
    # Asegurar que el directorio de portadas existe
    os.makedirs(Config.COVERS_DIR, exist_ok=True)

    # Determinar extensión del archivo de imagen
    original_name = item.get_name()
    _, ext = os.path.splitext(original_name)
    if not ext:
        # Intentar deducir de media_type
        media_type = getattr(item, "media_type", "image/jpeg")
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/svg+xml": ".svg",
        }
        ext = ext_map.get(media_type, ".jpg")

    # Generar nombre único con UUID
    unique_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(Config.COVERS_DIR, unique_name)

    # Escribir los bytes de la imagen
    with open(save_path, "wb") as f:
        f.write(item.get_content())

    # Retornar ruta relativa para almacenar en la BD
    # Formato: 'uploads/covers/uuid-filename.ext'
    return f"uploads/covers/{unique_name}"


# =============================================================================
# Función Principal de Parsing
# =============================================================================

def parse_epub(file_path: str) -> dict:
    """
    Lee un archivo .epub y extrae todos los metadatos disponibles
    junto con la imagen de portada.

    Args:
        file_path: Ruta absoluta al archivo .epub a procesar.

    Returns:
        dict: Diccionario con los metadatos extraídos:
            - title (str): Título de la obra.
            - author (str): Autor(es) de la obra.
            - publisher (str|None): Editorial.
            - language (str|None): Idioma.
            - isbn (str|None): Código ISBN.
            - cover_path (str|None): Ruta relativa de la imagen de portada.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        Exception: Si el archivo no es un ePub válido.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    # Leer el archivo ePub
    book = epub.read_epub(file_path, options={"ignore_ncx": True})

    # Extraer nombre del archivo original (para logging/debugging)
    epub_filename = os.path.basename(file_path)

    # Extraer metadatos Dublin Core
    metadata = {
        "title": _get_metadata_value(book, "title") or "Sin título",
        "author": _get_metadata_value(book, "creator") or "Autor desconocido",
        "publisher": _get_metadata_value(book, "publisher"),
        "language": _get_metadata_value(book, "language"),
        "isbn": _extract_isbn(book),
        "cover_path": _extract_cover_image(book),
        "format": "digital",  # Un ePub siempre es formato digital
    }

    return metadata


def delete_cover_file(cover_path: str) -> bool:
    """
    Elimina un archivo de portada del sistema de archivos.

    Args:
        cover_path: Ruta relativa de la portada (como se almacena en la BD).

    Returns:
        bool: True si se eliminó, False si no existía o hubo error.
    """
    if not cover_path:
        return False

    # Construir la ruta absoluta saneando el path para evitar Path Traversal
    safe_filename = os.path.basename(cover_path)
    full_path = os.path.join(Config.COVERS_DIR, safe_filename)

    try:
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except OSError as e:
        print(f"[WARN] No se pudo eliminar la portada: {e}")

    return False
