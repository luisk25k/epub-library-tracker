# -*- coding: utf-8 -*-
"""
Personal Library Tracker — Módulo de Base de Datos (models.py)
===============================================================
Gestiona la conexión a SQLite, la inicialización del esquema (tabla books,
triggers e índices) y provee funciones CRUD para interactuar con los datos.

Decisiones de diseño:
- Se usa sqlite3 nativo en lugar de un ORM para mantener el stack minimal.
- La BD se almacena en /database/library.db, ruta relativa al proyecto.
- Se habilita WAL mode para mejor rendimiento en lecturas concurrentes.
- row_factory = sqlite3.Row para acceder a columnas por nombre.
"""

import os
import sqlite3
from contextlib import contextmanager
from flask import g
from app.config import Config

# =============================================================================
# Configuración de la Base de Datos
# =============================================================================

# DDL: Definición del esquema de la tabla principal 'books'
# Incluye CHECK constraints para validar 'format' y 'reading_status'
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS books (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT    NOT NULL,
    author          TEXT    NOT NULL,
    publisher       TEXT    DEFAULT NULL,
    translator      TEXT    DEFAULT NULL,
    language        TEXT    DEFAULT NULL,
    isbn            TEXT    DEFAULT NULL UNIQUE,
    year_published  INTEGER DEFAULT NULL,
    num_pages       INTEGER DEFAULT NULL,
    format          TEXT    DEFAULT 'digital' CHECK(format IN ('digital', 'physical')),
    reading_status  TEXT    DEFAULT 'No leído' CHECK(reading_status IN ('No leído', 'Leyendo', 'Leído')),
    rating          INTEGER NOT NULL DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
    cover_path      TEXT    DEFAULT NULL,
    review          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime')),
    updated_at      TEXT    DEFAULT (strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime'))
);
"""

# Trigger para actualizar 'updated_at' automáticamente al modificar un registro
TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS update_books_timestamp
AFTER UPDATE ON books
FOR EACH ROW
BEGIN
    UPDATE books SET updated_at = strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime')
    WHERE id = OLD.id;
END;
"""

# Índices para optimizar búsquedas y filtrados frecuentes
INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);",
    "CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);",
    "CREATE INDEX IF NOT EXISTS idx_books_reading_status ON books(reading_status);",
]


# =============================================================================
# Conexión a la Base de Datos
# =============================================================================

def get_connection() -> sqlite3.Connection:
    """
    Retorna la conexión a la base de datos de la petición actual o crea una nueva si no existe.
    Configura ROWFactory para retornar diccionarios.
    """
    if 'db_conn' not in g:
        g.db_conn = sqlite3.connect(Config.DATABASE_PATH)
        g.db_conn.row_factory = sqlite3.Row
        
        # Activar soporte de llaves foráneas y modo WAL para mejor concurrencia
        g.db_conn.execute("PRAGMA foreign_keys = ON")
        g.db_conn.execute("PRAGMA journal_mode = WAL")
        
    return g.db_conn

def close_connection(e=None):
    """
    Cierra la conexión de la base de datos al finalizar la petición.
    (Debe ser registrada en app/__init__.py con teardown_appcontext)
    """
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close()

@contextmanager
def get_db():
    """
    Context manager para transacciones (commit automático o rollback).
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# =============================================================================
# Inicialización del Esquema
# =============================================================================

def init_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    os.makedirs(Config.DATABASE_DIR, exist_ok=True)
    with get_db() as db:
        # Crear tabla principal
        db.executescript(SCHEMA_SQL)

        # Crear trigger de actualización automática
        db.executescript(TRIGGER_SQL)

        # Crear índices de búsqueda
        for index_sql in INDEXES_SQL:
            db.execute(index_sql)
        db.execute("CREATE INDEX IF NOT EXISTS idx_books_year ON books(year_published)")
    print(f"[DB] Base de datos inicializada en: {Config.DATABASE_PATH}")


# =============================================================================
# Funciones CRUD — Books
# =============================================================================

def create_book(data: dict) -> int:
    """
    Inserta un nuevo libro en la base de datos.

    Args:
        data: Diccionario con las columnas del libro.
              Campos obligatorios: 'title', 'author'.
              Campos opcionales: 'publisher', 'translator', 'language',
              'isbn', 'year_published', 'num_pages', 'format',
              'reading_status', 'cover_path', 'review'.

    Returns:
        int: El ID del libro recién creado.

    Raises:
        sqlite3.IntegrityError: Si el ISBN ya existe en la BD.
    """
    columns = [
        "title", "author", "publisher", "translator", "language",
        "isbn", "year_published", "num_pages", "format",
        "reading_status", "rating", "cover_path", "review"
    ]

    # Filtrar solo las columnas presentes en el diccionario de datos
    present_cols = [col for col in columns if col in data and data[col] is not None]
    placeholders = ", ".join(["?"] * len(present_cols))
    col_names = ", ".join(present_cols)
    values = [data[col] for col in present_cols]

    sql = f"INSERT INTO books ({col_names}) VALUES ({placeholders})"

    with get_db() as db:
        cursor = db.execute(sql, values)
        return cursor.lastrowid


def get_all_books(search: str = None, status: str = None,
                  sort_by: str = "created_at", sort_dir: str = "desc",
                  limit: int = 20, offset: int = 0) -> list:
    """
    Obtiene todos los libros de la BD con soporte para búsqueda,
    filtrado por estatus y ordenación.

    Args:
        search:   Texto de búsqueda (coincidencia parcial en título y autor).
        status:   Filtro por estatus de lectura ('No leído', 'Leyendo', 'Leído').
        sort_by:  Campo por el cual ordenar ('title', 'author', 'created_at').
        sort_dir: Dirección de ordenación ('asc' o 'desc').

    Returns:
        list: Lista de diccionarios con los libros encontrados.
    """
    # Validar campos de ordenación para prevenir SQL injection
    valid_sort_fields = {"title", "author", "created_at", "year_published"}
    valid_sort_dirs = {"asc", "desc"}

    if sort_by not in valid_sort_fields:
        sort_by = "created_at"
    if sort_dir.lower() not in valid_sort_dirs:
        sort_dir = "desc"

    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    # Filtro de búsqueda (título o autor)
    if search:
        sql += " AND (title LIKE ? OR author LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern])

    # Filtro por estatus de lectura
    if status:
        sql += " AND reading_status = ?"
        params.append(status)

    # Ordenación
    sql += f" ORDER BY {sort_by} {sort_dir.upper()}"

    # Paginación
    if limit > 0:
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    with get_db() as db:
        rows = db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_book_by_id(book_id: int) -> dict:
    """
    Obtiene un libro específico por su ID.

    Args:
        book_id: ID del libro a buscar.

    Returns:
        dict: Diccionario con los datos del libro, o None si no existe.
    """
    with get_db() as db:
        row = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return dict(row) if row else None


def update_book(book_id: int, data: dict) -> bool:
    """
    Actualiza los campos de un libro existente.

    Args:
        book_id: ID del libro a actualizar.
        data:    Diccionario con los campos a modificar y sus nuevos valores.

    Returns:
        bool: True si se actualizó al menos un registro, False si el ID no existe.
    """
    if not data:
        return False

    # Construir SET clause dinámicamente según campos proporcionados
    set_clauses = []
    values = []
    for key, value in data.items():
        # Prevenir modificación de campos protegidos
        if key in ("id", "created_at", "updated_at"):
            continue
        set_clauses.append(f"{key} = ?")
        values.append(value)

    if not set_clauses:
        return False

    sql = f"UPDATE books SET {', '.join(set_clauses)} WHERE id = ?"
    values.append(book_id)

    with get_db() as db:
        cursor = db.execute(sql, values)
        return cursor.rowcount > 0


def delete_book(book_id: int) -> dict:
    """
    Elimina un libro de la BD y retorna sus datos (para permitir
    la eliminación del archivo de portada asociado).

    Args:
        book_id: ID del libro a eliminar.

    Returns:
        dict: Datos del libro eliminado, o None si no existía.
    """
    # Primero obtener los datos del libro (para cover_path)
    book = get_book_by_id(book_id)
    if not book:
        return None

    with get_db() as db:
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))

    return book
