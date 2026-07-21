# -*- coding: utf-8 -*-
"""
Personal Library Tracker — Routes (API REST + Vistas HTML)
============================================================
Define todos los endpoints de la aplicación:

API REST (JSON):
- POST   /api/books          → Crear libro (manual)
- POST   /api/books/upload   → Crear libro vía ePub upload
- GET    /api/books           → Listar libros (con búsqueda, filtro, orden)
- GET    /api/books/<id>      → Detalle de un libro
- PUT    /api/books/<id>      → Actualizar libro
- DELETE /api/books/<id>      → Eliminar libro

Vistas HTML (Server-Side Rendering):
- GET    /                    → Dashboard / Estantería (index.html)
- GET    /books/new           → Formulario de nuevo libro (book_form.html)
- GET    /books/<id>          → Vista detallada de un libro (book_detail.html)
- GET    /books/<id>/edit     → Formulario de edición (book_form.html)
"""

from flask import Blueprint, request, jsonify, render_template
from app.models import get_all_books, get_book_by_id
from app.services.book_service import (
    ingest_epub, create_book_manual, update_book_data, remove_book
)

# =============================================================================
# Blueprint Registration
# =============================================================================

main = Blueprint("main", __name__)


# =============================================================================
# Vistas HTML (Server-Side Rendering)
# =============================================================================

@main.route("/")
def index():
    """
    Dashboard principal — Vista de estantería (Grid).
    Soporta búsqueda, filtrado por estatus y ordenación vía query params.
    """
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    sort_by = request.args.get("sort_by", "created_at")
    sort_dir = request.args.get("sort_dir", "desc")

    books = get_all_books(
        search=search if search else None,
        status=status if status else None,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    return render_template(
        "index.html",
        books=books,
        search=search,
        status=status,
        sort_by=sort_by,
        sort_dir=sort_dir
    )


@main.route("/books/new")
def new_book():
    """Formulario para crear un nuevo libro (vacío)."""
    return render_template("book_form.html", book=None, editing=False)


@main.route("/books/<int:book_id>")
def book_detail(book_id):
    """Vista detallada de un libro específico."""
    book = get_book_by_id(book_id)
    if not book:
        return render_template("404.html"), 404
    return render_template("book_detail.html", book=book)


@main.route("/books/<int:book_id>/edit")
def edit_book(book_id):
    """Formulario para editar un libro existente (pre-rellenado)."""
    book = get_book_by_id(book_id)
    if not book:
        return render_template("404.html"), 404
    return render_template("book_form.html", book=book, editing=True)


# =============================================================================
# API REST — CRUD de Libros (JSON)
# =============================================================================

@main.route("/api/books", methods=["POST"])
def api_create_book():
    """
    POST /api/books — Crea un libro manualmente.

    Body (JSON):
        {
            "title": "string (obligatorio)",
            "author": "string (obligatorio)",
            "publisher": "string",
            "translator": "string",
            "language": "string",
            "isbn": "string",
            "year_published": int,
            "num_pages": int,
            "format": "digital|physical",
            "reading_status": "No leído|Leyendo|Leído",
            "review": "string (markdown)"
        }

    Returns:
        201: Libro creado exitosamente.
        400: Datos inválidos o campos obligatorios faltantes.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400

        result = create_book_manual(data)
        return jsonify(result), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@main.route("/api/books/upload", methods=["POST"])
def api_upload_epub():
    """
    POST /api/books/upload — Crea un libro vía subida de archivo ePub.

    Form Data:
        epub: archivo .epub

    Returns:
        201: Libro creado con metadatos extraídos.
        400: Archivo inválido o no proporcionado.
    """
    try:
        if "epub" not in request.files:
            return jsonify({"error": "No se proporcionó un archivo ePub"}), 400

        file = request.files["epub"]
        if file.filename == "":
            return jsonify({"error": "Nombre de archivo vacío"}), 400

        result = ingest_epub(file)
        return jsonify(result), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error al procesar el ePub: {str(e)}"}), 500


@main.route("/api/books", methods=["GET"])
def api_list_books():
    """
    GET /api/books — Lista todos los libros con búsqueda, filtros y ordenación.

    Query Params:
        search:   Texto a buscar en título/autor.
        status:   Filtrar por estatus ('No leído', 'Leyendo', 'Leído').
        sort_by:  Campo de ordenación ('title', 'author', 'created_at').
        sort_dir: Dirección ('asc', 'desc').

    Returns:
        200: Lista de libros en formato JSON.
    """
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    sort_by = request.args.get("sort_by", "created_at")
    sort_dir = request.args.get("sort_dir", "desc")

    books = get_all_books(
        search=search if search else None,
        status=status if status else None,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    return jsonify({"books": books, "total": len(books)})


@main.route("/api/books/<int:book_id>", methods=["GET"])
def api_get_book(book_id):
    """
    GET /api/books/<id> — Obtiene el detalle de un libro.

    Returns:
        200: Datos del libro.
        404: Libro no encontrado.
    """
    book = get_book_by_id(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404
    return jsonify(book)


@main.route("/api/books/<int:book_id>", methods=["PUT"])
def api_update_book(book_id):
    """
    PUT /api/books/<id> — Actualiza los datos de un libro.

    Body (JSON): Campos a actualizar (misma estructura que POST).

    Returns:
        200: Libro actualizado exitosamente.
        400: Datos inválidos.
        404: Libro no encontrado.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Se requiere un body JSON"}), 400

        result = update_book_data(book_id, data)
        return jsonify(result)

    except ValueError as e:
        error_msg = str(e)
        if "no encontrado" in error_msg.lower():
            return jsonify({"error": error_msg}), 404
        return jsonify({"error": error_msg}), 400
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@main.route("/api/books/<int:book_id>", methods=["DELETE"])
def api_delete_book(book_id):
    """
    DELETE /api/books/<id> — Elimina un libro y su portada asociada.

    Returns:
        200: Libro eliminado exitosamente.
        404: Libro no encontrado.
    """
    try:
        result = remove_book(book_id)
        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Error interno: {str(e)}"}), 500
