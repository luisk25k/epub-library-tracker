# Auditoría Técnica — Personal Library Tracker

> **Versión:** 1.0  
> **Fecha:** 2026-07-20  
> **Auditor:** Revisión automatizada de código  
> **Alcance:** Código fuente completo, dependencias, configuraciones y documentación

---

## 1. Propósito General

El **Personal Library Tracker** es una aplicación web CRUD monousuario, 100% local, diseñada para catalogar colecciones personales de libros físicos y digitales. Implementa un backend Flask con SQLite, parsing de metadatos ePub (vía `ebooklib`), autocompletado por ISBN (Google Books + OpenLibrary), y un frontend con TailwindCSS + JavaScript vanilla. Su objetivo es ofrecer un catálogo unificado, portable y privado, con espacio para reseñas en Markdown y seguimiento del estado de lectura.

---

## 2. Arquitectura y Flujo Lógico

### 2.1 Capas del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTE (Browser)                      │
│  HTML (Jinja2) + TailwindCSS + Vanilla JS + marked.js    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP (REST JSON + SSR)
┌──────────────────────▼──────────────────────────────────┐
│              FLASK — Application Factory                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  routes.py   │  │ book_service │  │  epub_parser   │  │
│  │  (Endpoints) │──▶│ (Lógica de   │  │  (Parsing ePub)│  │
│  │  REST + SSR  │  │  negocio)    │  └────────────────┘  │
│  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                               │
│         └─────────────────┘                               │
│                         │                                 │
│              ┌──────────▼──────────┐                      │
│              │    models.py         │                      │
│              │  (SQLite CRUD raw)   │                      │
│              └──────────┬──────────┘                      │
└─────────────────────────┼────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │   database/library.db  │  (SQLite WAL mode)
              └───────────────────────┘
                          │
              ┌───────────▼───────────┐
              │  uploads/covers/       │  (Imágenes locales)
              └───────────────────────┘
```

### 2.2 Ciclo de Vida de los Datos

1. **Ingesta:** El usuario sube un `.epub` → `routes.api_upload_epub` → `book_service.ingest_epub` → guarda temporal en disco → `epub_parser.parse_epub` extrae metadatos DC + portada → `models.create_book` persiste en SQLite → respuesta JSON con ID.
2. **Creación manual:** Formulario HTML → `submitBookForm()` JS → POST `/api/books` → `create_book_manual` valida → guarda portada si existe → `create_book`.
3. **Búsqueda ISBN:** Input ISBN → `fetchGoogleBooks()` JS → GET `/api/books/search?isbn=X` → `search_isbn` intenta OpenLibrary → Google Books pública → Google Books con API key → devuelve metadatos → JS autocompleta formulario.
4. **Visualización:** GET `/` → `get_all_books` con filtros → renderiza `index.html` (grid de portadas). GET `/books/<id>` → `get_book_by_id` → renderiza `book_detail.html` con reseña Markdown renderizada vía `marked.parse()`.
5. **Actualización:** Formulario de edición → PUT `/api/books/<id>` → `update_book_data` reemplaza portada si nueva → `update_book`.
6. **Eliminación:** Modal JS → DELETE `/api/books/<id>` → `remove_book` → `delete_book` (obtiene datos + borra registro) → elimina archivo de portada del disco.

### 2.3 Stack Tecnológico

| Capa         | Tecnología                      | Versión      |
| ------------ | ------------------------------- | ------------ |
| Backend      | Flask (Python 3.10+)            | 3.1.1        |
| BD           | SQLite 3 (WAL mode)             | Nativo       |
| ePub         | ebooklib + lxml                 | 0.18 / 5.4.0 |
| Frontend     | TailwindCSS CDN + marked.js CDN | —            |
| Dependencias | 11 paquetes (requirements.txt)  | Fijadas      |

---

## 3. Diagnóstico Crítico

### 3.1 Vulnerabilidades de Seguridad

| ID   | Severidad   | Hallazgo                                                                                                                                                                                                                                                                                                        | Archivo/Línea                                  |
| ---- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| S-01 | **CRÍTICO** | API Key de Google Books hardcodeada en `.env` dentro del repositorio. Aunque `.env` está en `.gitignore`, si alguien ejecuta la app sin sobrescribir el `.env.example`, la key `AIzaSyAw_bTjlt_xICXfQXcosTmPtjjVuZEXHFw` queda expuesta. Debería eliminarse del control de versiones.                           | `.env:1`                                       |
| S-02 | **ALTO**    | `SECRET_KEY` hardcodeada como string literal en `app/__init__.py:32`. Flask usa esta clave para firmar sesiones y tokens. Debe cargarse desde variable de entorno.                                                                                                                                              | `app/__init__.py:32`                           |
| S-03 | **ALTO**    | **Sin protección CSRF.** Los formularios se envían vía JS con `fetch()`, pero el backend no valida ningún token CSRF. Un ataque CSRF podría crear/modificar/eliminar libros en un navegador autenticado (aunque sea local, es una vulnerabilidad estándar).                                                     | `app/routes.py` (todos los endpoints mutantes) |
| S-04 | **ALTO**    | **XSS almacenado en reseñas Markdown.** `marked.setOptions({sanitize: false})` en `app/static/js/app.js:265` desactiva la sanitización. Aunque el sistema es local, si un usuario malicioso inserta `<script>` en la reseña y otro usuario (o incluso el mismo) visualiza el detalle, se ejecuta JS arbitrario. | `app/static/js/app.js:265`                     |
| S-05 | **MEDIO**   | **Posible path traversal en `delete_cover_file`.** La función recibe `cover_path` relativo y construye la ruta absoluta sin sanitizar. Si `cover_path` contiene `../`, podría eliminar archivos fuera del directorio de covers.                                                                                 | `app/services/epub_parser.py:254`              |
| S-06 | **MEDIO**   | **Subida de archivos sin validación MIME real.** Solo se valida la extensión `.epub` y el tamaño. No se verifica el content-type MIME ni se escanea el contenido. Un archivo malicioso renombrado a `.epub` pasaría la validación.                                                                              | `app/services/book_service.py:95-96`           |
| S-07 | **BAJO**    | **Contenido de portada sin validación.** En `_save_cover_image`, se escribe directamente el contenido binario extraído del ePub sin validar que sea una imagen válida. Podría escribirse cualquier tipo de archivo.                                                                                             | `app/services/epub_parser.py:183-185`          |

### 3.2 Errores Lógicos

| ID   | Severidad       | Hallazgo                                                                                                                                                                                                                                                              | Archivo/Línea                                   |
| ---- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| L-01 | **MEDIO**       | **`replace("uploads/covers/", "uploads/covers/")` es un no-op.** La línea `cover_path.replace("uploads/covers/", "uploads/covers/")` reemplaza una string por sí misma, no hace nada. Probablemente se pretendía extraer el nombre del archivo para la ruta absoluta. | `app/services/epub_parser.py:254`               |
| L-02 | **MEDIO**       | **Parámetro `epub_filename` no utilizado.** La función `_extract_cover_image` recibe `epub_filename` como argumento (`epub_parser.py:224`) pero nunca lo usa. Es código muerto.                                                                                       | `app/services/epub_parser.py:137,224,233`       |
| L-03 | **BAJO**        | **`isbn` vacío como string ("") pasa la validación.** Si el formulario envía `isbn=""` (string vacío), no hay null check. Se almacena como `""` en lugar de `NULL`, pero la columna tiene UNIQUE, lo que impediría tener dos libros con ISBN vacío.                   | `app/services/book_service.py:132`              |
| L-04 | **BAJO**        | **Rating default inconsistente.** El DDL en `models.py:28` define `DEFAULT 0`, pero `requerimientos_v2.md:22` especifica `DEFAULT 1`. El frontend muestra estrellas 1-5 pero permite rating=0.                                                                        | `app/models.py:28` vs `requerimientos_v2.md`    |
| L-05 | **BAJO**        | **Descarga de portada externa silenciosamente ignorada.** En `create_book_manual` y `update_book_data`, si `download_external_cover` falla, se captura `Exception` y se ignora con `pass`. El usuario no recibe feedback de que la portada no pudo descargarse.       | `app/services/book_service.py:158-160, 189-191` |
| L-06 | **BAJO**        | **`format` no se asigna por defecto en ingesta manual.** En `create_book_manual`, si el usuario no selecciona formato, no se establece valor y la BD usará `DEFAULT 'digital'`. Correcto, pero la capa de servicio debería explicitarlo para claridad.                | `app/services/book_service.py:122`              |
| L-07 | **INFORMATIVO** | **`created_at`/`updated_at` no son estrictamente ISO 8601.** Usan `strftime` con `localtime` pero sin zona horaria. Son cadenas como `2026-07-20T21:00:00` sin offset. Para una app local no es crítico, pero es impreciso.                                           | `app/models.py:32-33`                           |

### 3.3 Anti-Patrones

| ID   | Severidad | Hallazgo                                                                                                                                                                                                                                                                                        | Archivo/Línea                             |
| ---- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| A-01 | **ALTO**  | **`BASE_DIR` y `COVERS_DIR` calculados a nivel de módulo.** En `epub_parser.py:23-24`, se calculan rutas absolutas en tiempo de importación. Si la estructura del proyecto cambia o se importa desde un contexto diferente, las rutas serán incorrectas. Deberían ser parámetros configurables. | `app/services/epub_parser.py:23-24`       |
| A-02 | **MEDIO** | **Duplicación de cálculo de `BASE_DIR`.** El mismo patrón `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` se repite en 3 módulos: `models.py:20`, `book_service.py:68`, `epub_parser.py:23`. Debería centralizarse en `app/__init__.py` o en un módulo `config.py`.               | Múltiples                                 |
| A-03 | **MEDIO** | **Conexiones BD sin pool.** Se crea una nueva conexión SQLite por cada operación CRUD (`get_db()`). Para una app monousuario local no es un problema grave, pero el patrón correcto sería reutilizar la conexión y usar pooling.                                                                | `app/models.py:50-68`                     |
| A-04 | **MEDIO** | **`init_db()` ejecutado en cada arranque.** Se llama DDL con `CREATE IF NOT EXISTS`, índices y triggers en cada inicio. Innecesario después de la primera ejecución; ralentiza el arranque.                                                                                                     | `app/__init__.py:36` → `app/models.py:93` |
| A-05 | **BAJO**  | **Manejo inconsistente de `sort_dir`.** Se usa `sort_dir.lower()` en `get_all_books` (`models.py:127`) pero no en `index()` de routes. Tampoco se valida con un set antes de la interpolación; se hace después.                                                                                 | `app/models.py:127`                       |
| A-06 | **BAJO**  | **`onchange="this.form.submit()"` en selects HTML.** Mezcla lógica de presentación con comportamiento. Debería manejarse con event listeners en JS.                                                                                                                                             | `app/templates/index.html:39,50,60`       |
| A-07 | **BAJO**  | **CSS sin fingerprint/cache busting.** Archivos estáticos servidos sin hash en la URL. Podrían servirse versiones cacheadas tras cambios.                                                                                                                                                       | `app/templates/base.html:34`              |
| A-08 | **BAJO**  | **CDNs sin integridad SRI.** TailwindCSS y marked.js se cargan vía CDN sin atributos `integrity`. Un ataque al CDN compromete toda la app.                                                                                                                                                      | `app/templates/base.html:15,101`          |

### 3.4 Cuellos de Botella de Rendimiento

| ID   | Severidad | Hallazgo                                                                                                                                                                                                                                            | Archivo/Línea                          |
| ---- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| P-01 | **ALTO**  | **Sin paginación en `get_all_books`.** La función retorna TODOS los libros de la BD sin límite. Con una colección grande (>5000 libros), la memoria y el tiempo de respuesta se degradan severamente.                                               | `app/models.py:107-134`                |
| P-02 | **MEDIO** | **Búsqueda ISBN secuencial en lugar de paralela.** `search_isbn` hace 3-5 llamadas HTTP bloqueantes secuenciales (OpenLibrary → Google Books pública × 2 → Google Books con key × 2). Podría lanzarse en paralelo con `concurrent.futures`.         | `app/services/book_service.py:199-255` |
| P-03 | **BAJO**  | **Conversión `dict(row)` en cada `get_all_books`.** `[dict(row) for row in rows]` itera todas las filas y construye diccionarios. Con SQLite.Row esto no es un gran problema, pero es un overhead evitable cuando solo se necesitan ciertos campos. | `app/models.py:133`                    |
| P-04 | **BAJO**  | **`init_db()` ejecuta `executescript` con múltiples statements.** Aunque es idempotente, sigue parseando y ejecutando comandos DDL en cada startup.                                                                                                 | `app/models.py:95-103`                 |
| P-05 | **BAJO**  | **Subida de ePub: guarda en disco antes de validar.** En `ingest_epub`, primero se guarda el archivo temporal en disco (`file_storage.save(temp_path)`) y luego se valida el tamaño. Debería validarse antes de escribir.                           | `app/services/book_service.py:101-104` |

---

## 4. Plan de Refactorización

### 4.1 Correcciones de Seguridad (Prioridad Inmediata)

| #   | Acción                                                                                                                                                                                                   | Archivo                                  | Esfuerzo |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | -------- |
| 1   | Eliminar `.env` con API Key real del repo y añadirlo a `.gitignore` (ya está). La API key debe rotarse en Google Cloud Console.                                                                          | `.env`                                   | 5 min    |
| 2   | Mover `SECRET_KEY` a variable de entorno. En desarrollo, leer de `os.environ.get('SECRET_KEY')` con fallback a un valor solo si `FLASK_ENV=development`.                                                 | `app/__init__.py:32`                     | 10 min   |
| 3   | Implementar CSRF protection con `flask-wtf` o generando tokens manualmente. Alternativa: usar `request.headers.get('X-Requested-With') === 'XMLHttpRequest'` como validación mínima para endpoints AJAX. | `app/routes.py` + `app/static/js/app.js` | 2-4 h    |
| 4   | Aplicar sanitización DOMPurify al contenido Markdown renderizado. Cambiar `sanitize: false` por DOMPurify post-render, o migrar a renderizado server-side con `markdown` + `bleach`.                     | `app/static/js/app.js:265` + templates   | 2-3 h    |
| 5   | Sanitizar `cover_path` en `delete_cover_file`: rechazar rutas con `..` o caracteres peligrosos. Usar `os.path.basename` combinado con `os.path.join` controlado.                                         | `app/services/epub_parser.py:254`        | 15 min   |
| 6   | Agregar validación MIME real en subida de archivos usando `python-magic` o verificando header `%PDF`/`PK` (ZIP)                                                                                          | `app/services/book_service.py:95-96`     | 1 h      |

### 4.2 Correcciones de Errores Lógicos

| #   | Acción                                                                                                          | Archivo                                         | Esfuerzo |
| --- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------- |
| 7   | Corregir `delete_cover_file`: reemplazar el `replace` por `os.path.basename` o construir la ruta correctamente. | `app/services/epub_parser.py:254`               | 5 min    |
| 8   | Eliminar el parámetro `epub_filename` (y la variable local) de `_extract_cover_image` y su llamado.             | `app/services/epub_parser.py:137,224,233`       | 5 min    |
| 9   | Agregar normalización de ISBN vacío a `None` en la capa de servicio.                                            | `app/services/book_service.py:132`              | 10 min   |
| 10  | Unificar criterio de rating: decidir entre `DEFAULT 0` o `DEFAULT 1` y sincronizar DDL + documentación.         | `app/models.py:28` + docs                       | 10 min   |
| 11  | Agregar feedback al usuario cuando falla la descarga de portada externa (log + mensaje informativo).            | `app/services/book_service.py:158-160, 189-191` | 30 min   |

### 4.3 Refactorización de Anti-Patrones (Mantenibilidad)

| #   | Acción                                                                                                                                                        | Archivo                                                      | Esfuerzo |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------- |
| 12  | Centralizar `BASE_DIR` y rutas del proyecto en un módulo `app/config.py`. Calcular rutas una vez al crear la app, no en tiempo de importación de cada módulo. | `app/__init__.py` + nuevo `app/config.py`                    | 30 min   |
| 13  | Refactorizar `get_db()` para compartir conexión SQLite a nivel de request (usar `g` de Flask o `after_request`).                                              | `app/models.py` + `app/__init__.py`                          | 1 h      |
| 14  | Separar `init_db()` de la creación de la app. Llamarlo explícitamente solo cuando sea necesario (por CLI, por migración).                                     | `app/__init__.py:36` → `run.py`                              | 15 min   |
| 15  | Mover event handlers de HTML (`onchange`) a JavaScript con `addEventListener`.                                                                                | `app/templates/index.html:39,50,60` + `app/static/js/app.js` | 1 h      |
| 16  | Agregar `integrity` hashes a los scripts CDN. Usar `flask-caching` para cache busting de estáticos.                                                           | `app/templates/base.html:15,101`                             | 15 min   |

### 4.4 Optimizaciones de Rendimiento

| #   | Acción                                                                                                                                                                        | Archivo                                  | Esfuerzo |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | -------- |
| 17  | Implementar paginación en `get_all_books` con parámetros `page` y `per_page`. Agregar `LIMIT`/`OFFSET` en SQL. Actualizar frontend para carga progresiva o paginación visual. | `app/models.py:107-134` + templates + JS | 4-6 h    |
| 18  | Paralelizar búsqueda ISBN con `concurrent.futures.ThreadPoolExecutor`. Lanzar OpenLibrary + Google Books (con/sin key) en paralelo y tomar el primer resultado exitoso.       | `app/services/book_service.py:199-255`   | 2-3 h    |
| 19  | Agregar límite de consultas SQL en `get_all_books` incluso sin paginación (ej. `LIMIT 200` por defecto).                                                                      | `app/models.py:107-134`                  | 15 min   |
| 20  | Validar tamaño del archivo ePub antes de guardarlo en disco (`file_storage.content_length` o `file.seek(0,2)` primero).                                                       | `app/services/book_service.py:101-104`   | 10 min   |

### 4.5 Aplicación de Principios SOLID y Clean Code

| Principio                       | Situación Actual                                                                                                                                 | Acción Recomendada                                                                                                                                                 |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **SRP** (Single Responsibility) | `book_service.py` maneja descarga de imágenes, validación, parsing de tipos, y lógica de negocio.                                                | Separar en: `ImageService` (save/download cover), `ValidationService` (input validation), `BookService` (orquestación pura).                                       |
| **OCP** (Open/Closed)           | Las funciones de búsqueda en `search_isbn` son un if-else secuencial de estrategias.                                                             | Implementar patrón **Strategy** con clases `MetadataProvider` (OpenLibraryProvider, GoogleBooksProvider). Nuevas fuentes se añaden sin modificar código existente. |
| **DIP** (Dependency Inversion)  | `routes.py` importa directamente `models.py` y `book_service.py`.                                                                                | Inyectar dependencias a través del constructor de la app. Más fácil si se desea testear con BD mock.                                                               |
| **DRY**                         | Cálculo de `BASE_DIR` repetido 3 veces, lógica de validación de `rating`/`year_published` repetida en `create_book_manual` y `update_book_data`. | Extraer validadores reutilizables (`validate_rating`, `validate_year`).                                                                                            |
| **KISS**                        | `search_isbn` tiene 3 niveles de anidamiento (intentos, try/except, helper interno).                                                             | Simplificar con early returns y estrategias paralelas.                                                                                                             |
| **Error Handling**              | Múltiples `except: pass` silencian fallos.                                                                                                       | Siempre loggear errores con `app.logger.error()` antes de `pass`. Solo callar excepciones esperadas y conocidas.                                                   |

### 4.6 Hoja de Ruta Recomendada

```
Fase 1 — Crítico (1-2 días)
├── S-01 Rotar API Key + asegurar .env
├── S-02 Mover SECRET_KEY a variable de entorno
├── S-04 Sanitizar Markdown (DOMPurify / server-side)
├── L-01/L-02 Corregir bugs en delete_cover_file y parámetro muerto
└── P-01 Paginación básica en get_all_books

Fase 2 — Alta (2-3 días)
├── S-03 Implementar CSRF protection
├── S-05 Sanitizar path en delete_cover_file
├── A-01/A-02 Centralizar configuración en app/config.py
├── A-03 Refactorizar conexión BD (pool/request-scoped)
└── P-02 Paralelizar búsqueda ISBN

Fase 3 — Media (3-5 días)
├── S-06/S-07 Validación MIME + contenido imagen
├── A-04 Separar init_db() del startup
├── A-05/A-06 Refactorizar event handlers a JS
├── A-08 Agregar SRI hashes a CDNs
├── P-05 Validar tamaño ePub antes de guardar
└── 4.5 Aplicar principios SOLID (Strategy, SRP separación)

Fase 4 — Baja / Mejora Continua
├── L-07 Normalizar fechas a ISO 8601 con timezone
├── A-07 Implementar cache busting de estáticos
├── Agregar tests unitarios (pytest) para modelos y servicios
├── Agregar type hints completos (mypy compliance)
└── Migrar a FastAPI si se requiere documentación OpenAPI nativa
```

---

_Fin del reporte de auditoría técnica. Este documento no modifica ningún archivo del código fuente del proyecto._
