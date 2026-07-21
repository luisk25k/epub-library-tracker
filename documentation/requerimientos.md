# Personal Library Tracker — Documento de Requerimientos

> **Versión:** 1.0  
> **Fecha:** 2026-07-20  
> **Autor:** Arquitectura de Software  
> **Estado:** Fase 1 — Asimilación y Documentación

---

## 1. Propósito General

El **Personal Library Tracker** es un sistema web CRUD, ligero y privado, diseñado para gestionar una colección personal de libros digitales y físicos. Su razón de ser es resolver un problema concreto: la falta de un catálogo unificado, portable y con capacidad de análisis crítico para bibliotecas personales.

### Problema que resuelve

- **Fragmentación del inventario:** Los lectores con colecciones extensas carecen de una herramienta que unifique libros físicos y digitales en un único registro consultable.
- **Pérdida de metadatos:** La catalogación manual es tediosa y propensa a errores. Los archivos `.epub` contienen metadatos valiosos (título, autor, portada) que pueden extraerse automáticamente.
- **Ausencia de espacio crítico:** Las plataformas comerciales (Goodreads, StoryGraph) no ofrecen un entorno privado y flexible para notas de carácter filológico, histórico o de análisis crítico profundo.
- **Dependencia de servicios externos:** El sistema opera de manera completamente local, sin cuentas, sin telemetría y sin dependencias de terceros en tiempo de ejecución.

### Principios de Diseño

| Principio | Descripción |
|---|---|
| **Portabilidad** | Base de datos SQLite en un único archivo. Todo el sistema empaquetable y transportable. |
| **Privacidad** | Operación 100% local. Sin conexiones externas, sin tracking, sin cuentas de usuario. |
| **Ligereza** | Stack mínimo, sin frameworks pesados del lado del cliente. Arranque instantáneo. |
| **Rigor catalográfico** | Campos dedicados a editorial, traductor y edición, orientados a una catalogación seria. |

---

## 2. Alcance y Funcionalidades Core

### 2.1 Módulo de Ingesta (ePub Parsing)

El sistema debe permitir la subida de archivos `.epub` y extraer automáticamente la información contenida en sus metadatos OPF/Dublin Core.

| Funcionalidad | Detalle |
|---|---|
| **Subida de archivo** | Formulario para cargar un archivo `.epub` desde el sistema de archivos local. |
| **Extracción de título** | Lectura automática del campo `<dc:title>` del manifiesto OPF. |
| **Extracción de autor** | Lectura automática del campo `<dc:creator>` del manifiesto OPF. |
| **Extracción de portada** | Identificación y extracción de la imagen de portada declarada en el manifiesto (`cover-image`, `cover`). Almacenamiento local de la imagen. |
| **Extracción de editorial** | Lectura del campo `<dc:publisher>`, si está disponible. |
| **Extracción de idioma** | Lectura del campo `<dc:language>`, si está disponible. |
| **Extracción de ISBN** | Lectura del campo `<dc:identifier>` con esquema ISBN, si está disponible. |
| **Edición post-ingesta** | Todos los campos extraídos deben ser editables manualmente tras la importación, ya que los metadatos embebidos pueden ser incompletos o erróneos. |

### 2.2 CRUD de Libros (Gestión del Catálogo)

Operaciones completas de Crear, Leer, Actualizar y Eliminar sobre los registros de libros.

- **Crear:** Manualmente (formulario vacío) o vía ingesta de `.epub` (formulario pre-rellenado con metadatos extraídos).
- **Leer:** Visualización individual detallada de cada libro y vista general del catálogo.
- **Actualizar:** Edición de todos los campos de un registro existente, incluyendo la posibilidad de reemplazar la imagen de portada.
- **Eliminar:** Borrado de un registro con confirmación previa. La eliminación debe borrar también la imagen de portada asociada del almacenamiento local.

### 2.3 Gestión del Estatus de Lectura

Cada libro debe tener un campo de estatus de lectura con los siguientes valores predefinidos:

| Estatus | Descripción |
|---|---|
| `No leído` | El libro está en la colección pero no se ha comenzado. |
| `Leyendo` | Lectura en curso. |
| `Leído` | Lectura completada. |

- El estatus debe ser seleccionable mediante un desplegable (`<select>`).
- El estatus debe reflejarse visualmente en la vista de cuadrícula (por ejemplo, mediante una etiqueta de color o un indicador en la tarjeta de portada).

### 2.4 Gestión de Reseñas (CRUD)

Cada libro debe tener un espacio asociado para escribir, editar y eliminar reseñas o notas personales.

- **Formato:** Texto enriquecido vía Markdown. El sistema debe renderizar Markdown a HTML para la visualización.
- **Enfoque:** El espacio está orientado a notas de análisis crítico, filológico e histórico, no a reseñas casuales. Debe soportar texto extenso sin degradación de rendimiento.
- **Operaciones:** Crear, leer, editar y eliminar la reseña asociada a un libro.
- **Persistencia:** Las reseñas se almacenan directamente en la base de datos como texto Markdown.

### 2.5 Dashboard / Interfaz de Estantería

La interfaz principal del sistema es una vista de cuadrícula (Grid) que simula una estantería digital.

- **Vista de cuadrícula:** Tarjetas mostrando la imagen de portada, el título y el autor de cada libro.
- **Indicador visual de estatus:** Cada tarjeta debe mostrar visualmente el estatus de lectura (No leído / Leyendo / Leído) mediante un badge o etiqueta de color.
- **Acceso al detalle:** Click en una tarjeta para acceder a la vista completa del libro (todos los campos + reseña).
- **Búsqueda y filtrado:** Campo de búsqueda por título y/o autor. Filtro por estatus de lectura.
- **Ordenación:** Por título, autor o fecha de adición al catálogo.
- **Portada por defecto:** Si un libro no tiene imagen de portada (ingreso manual sin imagen), el sistema debe mostrar un placeholder genérico.

---

## 3. Arquitectura / Stack Tecnológico

### 3.1 Visión General

```
┌─────────────────────────────────────────────────┐
│                   CLIENTE                       │
│  HTML5 + TailwindCSS + Vanilla JavaScript       │
│  (Renderizado de Markdown con marked.js o       │
│   similar en el cliente)                        │
└────────────────────┬────────────────────────────┘
                     │  HTTP (REST API / JSON)
                     │
┌────────────────────▼────────────────────────────┐
│                  SERVIDOR                       │
│  Python (Flask o FastAPI)                       │
│  ├── Rutas / Endpoints REST                     │
│  ├── Lógica de negocio                          │
│  ├── Módulo de parsing ePub (ebooklib / lxml)   │
│  └── ORM / Acceso a datos (SQLAlchemy o raw)    │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│              BASE DE DATOS                      │
│  SQLite (archivo único .db)                     │
│  └── Almacenamiento de metadatos y reseñas      │
└─────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│          SISTEMA DE ARCHIVOS LOCAL              │
│  └── /uploads/covers/ (imágenes de portada)     │
└─────────────────────────────────────────────────┘
```

### 3.2 Detalle del Stack

| Capa | Tecnología | Justificación |
|---|---|---|
| **Backend** | Python 3.10+ con **Flask** o **FastAPI** | Microframeworks ligeros. Flask por simplicidad; FastAPI por tipado y docs automáticos (OpenAPI). Decisión a tomar en Fase 2. |
| **Base de datos** | **SQLite 3** | Cero configuración, archivo único portable, ideal para aplicaciones de un solo usuario. |
| **ORM / DB Access** | **SQLAlchemy** (opcional) o `sqlite3` nativo | SQLAlchemy para migraciones y abstracción; `sqlite3` nativo si se prioriza simplicidad absoluta. |
| **ePub Parsing** | **ebooklib** (`EpubBook`) | Librería Python madura para lectura y extracción de metadatos y recursos de archivos `.epub`. |
| **Frontend** | **HTML5** + **TailwindCSS** (CDN o build) + **Vanilla JS** | Sin frameworks JS pesados. TailwindCSS para utilidades de estilo rápidas. JavaScript puro para interactividad. |
| **Renderizado Markdown** | **marked.js** (cliente) o **markdown2** / **mistune** (servidor) | Conversión de Markdown a HTML para las reseñas. Preferiblemente en el cliente para reducir carga del servidor. |
| **Servidor de desarrollo** | Servidor integrado de Flask/FastAPI | Para ejecución local. Sin necesidad de Nginx/Apache. |

### 3.3 Estructura de Directorios Propuesta

```
epub-library-tracker/
├── app/
│   ├── __init__.py            # Inicialización de la app Flask/FastAPI
│   ├── models.py              # Definición de modelos / esquema de BD
│   ├── routes.py              # Endpoints de la API REST
│   ├── services/
│   │   ├── __init__.py
│   │   ├── epub_parser.py     # Módulo de ingesta y parsing de ePub
│   │   └── book_service.py    # Lógica de negocio para libros
│   ├── static/
│   │   ├── css/               # Estilos (TailwindCSS compilado o CDN)
│   │   ├── js/                # JavaScript vanilla
│   │   └── uploads/
│   │       └── covers/        # Imágenes de portada extraídas/subidas
│   └── templates/
│       ├── base.html           # Template base con layout
│       ├── index.html          # Dashboard / Estantería
│       ├── book_detail.html    # Vista detallada de un libro
│       └── book_form.html      # Formulario de creación/edición
├── database/
│   └── library.db              # Archivo SQLite (generado en runtime)
├── requerimientos.md           # Este documento
├── requirements.txt            # Dependencias Python
└── run.py                      # Punto de entrada de la aplicación
```

---

## 4. Esquema de Datos Preliminar

### 4.1 Tabla: `books`

Tabla principal que almacena la información catalográfica de cada libro.

| Columna | Tipo SQLite | Restricciones | Descripción |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador único del registro. |
| `title` | `TEXT` | `NOT NULL` | Título de la obra. |
| `author` | `TEXT` | `NOT NULL` | Autor o autores de la obra. |
| `publisher` | `TEXT` | `DEFAULT NULL` | Editorial (ej. Alianza, Penguin, Alba, Páginas de Espuma). |
| `translator` | `TEXT` | `DEFAULT NULL` | Nombre del traductor, si aplica (ej. Gregorio Canteras). Campo clave para asegurar la fiabilidad textual de traducciones. |
| `language` | `TEXT` | `DEFAULT NULL` | Idioma de la edición (código ISO 639-1 o nombre completo). |
| `isbn` | `TEXT` | `DEFAULT NULL, UNIQUE` | Código ISBN-10 o ISBN-13. |
| `year_published` | `INTEGER` | `DEFAULT NULL` | Año de publicación de la edición. |
| `num_pages` | `INTEGER` | `DEFAULT NULL` | Número de páginas (para ediciones físicas o referencia). |
| `format` | `TEXT` | `DEFAULT 'digital'` | Formato del ejemplar: `'digital'` (ePub, PDF, etc.) o `'physical'`. |
| `reading_status` | `TEXT` | `DEFAULT 'No leído'` | Estatus de lectura: `'No leído'`, `'Leyendo'`, `'Leído'`. |
| `cover_path` | `TEXT` | `DEFAULT NULL` | Ruta relativa a la imagen de portada almacenada localmente. |
| `review` | `TEXT` | `DEFAULT NULL` | Reseña / notas personales en formato Markdown. Orientado a análisis crítico, filológico e histórico. |
| `created_at` | `TEXT` | `DEFAULT CURRENT_TIMESTAMP` | Fecha y hora de creación del registro (formato ISO 8601). |
| `updated_at` | `TEXT` | `DEFAULT CURRENT_TIMESTAMP` | Fecha y hora de la última actualización del registro. |

### 4.2 DDL Preliminar (SQLite)

```sql
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
    cover_path      TEXT    DEFAULT NULL,
    review          TEXT    DEFAULT NULL,
    created_at      TEXT    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TEXT    DEFAULT CURRENT_TIMESTAMP
);

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER IF NOT EXISTS update_books_timestamp
AFTER UPDATE ON books
FOR EACH ROW
BEGIN
    UPDATE books SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Índices para búsqueda y filtrado
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_reading_status ON books(reading_status);
```

### 4.3 Notas sobre el Esquema

- **Tabla única por simplicidad:** En esta versión inicial, todos los datos del libro incluyendo la reseña residen en una sola tabla. Si en el futuro se requiere un sistema de múltiples reseñas por libro o un historial de notas, se extraería `review` a una tabla `reviews` con relación `1:N`.
- **Campo `translator`:** Decisión deliberada de incluirlo como campo de primer nivel. En el ámbito filológico, la elección del traductor define la calidad y fidelidad del texto. No es un dato secundario.
- **Campo `format`:** Permite distinguir entre ejemplares digitales y físicos dentro de la misma colección.
- **Markdown en `review`:** Se almacena como texto plano Markdown. El renderizado a HTML se realiza en el momento de la visualización (cliente o servidor), nunca se almacena HTML renderizado.
- **`cover_path` como ruta relativa:** Almacenar rutas relativas (ej. `covers/uuid-filename.jpg`) en lugar de absolutas, para mantener la portabilidad del sistema.

---

## 5. Restricciones y Consideraciones

| Aspecto | Restricción |
|---|---|
| **Usuarios** | Sistema mono-usuario. No se contempla autenticación ni gestión de sesiones. |
| **Red** | Operación exclusivamente local (`localhost`). No se expone a red pública. |
| **Formatos soportados** | Ingesta automática solo para `.epub`. Otros formatos (PDF, MOBI) se registran manualmente. |
| **Tamaño de archivos** | Considerar un límite razonable para la subida de `.epub` (ej. 50 MB). |
| **Imágenes de portada** | Se almacenan como archivos estáticos en el sistema de archivos, no como BLOBs en SQLite. |
| **Backup** | La portabilidad inherente de SQLite (un solo archivo `.db`) facilita el respaldo manual. |

---

*Fin del documento de requerimientos — Fase 1 completada.*
