# Requerimientos V3 - Personal Library Tracker (Anexo)

Este documento sirve como anexo a los requerimientos base del proyecto, detallando exclusivamente la integración del módulo de importación masiva mediante archivos CSV generados por Goodreads.

## 1. Módulo de Importación Masiva (Goodreads CSV)

### 1.1 Frontend
- **Interfaz de Usuario:** El sistema debe incluir una vista o un botón/modal de "Importar Biblioteca" accesible de manera clara desde la interfaz principal.
- **Entrada de Datos:** Debe permitir al usuario subir un archivo con extensión `.csv` (nativo de exportación de Goodreads) utilizando un `<input type="file" accept=".csv">`.
- **Feedback Visual:** Se debe mostrar una barra de progreso o un mensaje de éxito/error en JavaScript Vanilla para informar al usuario sobre el estado del procesamiento.

### 1.2 Backend
- **Endpoint API:** Se debe crear un endpoint dedicado, por ejemplo, `POST /api/import-csv`.
- **Procesamiento de Archivos:** El backend en Python utilizará la librería estándar `csv` (u otra nativa) para leer y procesar el archivo subido.
- **Mapeo de Datos:** El backend debe transformar los datos (manejando correctamente nulos o vacíos) y mapear las columnas específicas de Goodreads a la base de datos SQLite de la siguiente manera:
  - `Title` ➔ Título (`title`)
  - `Author` ➔ Autor (`author`)
  - `ISBN13` o `ISBN` ➔ ISBN (`isbn`) — *Priorizando ISBN13 si ambos están presentes.*
  - `Publisher` ➔ Editorial (`publisher`)
  - `My Rating` ➔ Puntuación / Rating (`rating`) — *(Valores 1-5, o 0 si no tiene).*
  - `My Review` ➔ Reseña / Notas personales (`review`)
  - `Bookshelves` o `Exclusive Shelf` ➔ Estatus de Lectura (`reading_status`). Mapeo esperado:
    - `"read"` ➔ `"Leído"`
    - `"currently-reading"` ➔ `"Leyendo"`
    - `"to-read"` ➔ `"No leído"`
    - *(Si el estatus no coincide o está vacío, asignar "No leído" por defecto).*
- **Inserción Segura y Prevención de Duplicados:**
  - El sistema procesará las filas e insertará los registros en lote (bulk insert) o mediante iteración transaccional segura en SQLite.
  - Se deben omitir los duplicados. La verificación de duplicidad se realizará comprobando la preexistencia del `ISBN` (si existe y es válido) o del `Título` (si el ISBN está vacío).
